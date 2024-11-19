""" update currency is meant as a cron job to update the currencies in the database
    used in howdimain for table stock_currency. It is not using the Django ORM
    but directly with sql.
"""

from decouple import config
import datetime
from datetime import timezone
import requests
import psycopg
from howdimain.utils.plogger import Logger

logformat = "%(asctime)s:%(levelname)s:%(message)s"
Logger.set_logger(config("LOG_FILE"), logformat, "INFO")
logger = Logger.getlogger()


class UpdateCurrencies:
    host = "localhost"
    db_port = config("DB_PORT")
    db_user = config("DB_USER")
    db_user_pw = config("DB_PASSWORD")
    database = config("DB_NAME")
    table_currency = "stock_currency"
    table_currencyhistory = "stock_currencyhistory"

    access_key = config("access_key_currency")
    # forex_url = 'http://api.currencylayer.com/live'
    forex_url = "http://apilayer.net/api/live"

    @classmethod
    def update_currencies(cls):
        utc_date = datetime.datetime.now(timezone.utc).date()
        logger.info(
            f"{utc_date.strftime('%d-%m-%Y')}: update currencies using {cls.forex_url}"
        )

        connect_string = (
            f"host='{cls.host}' port='{cls.db_port}' "
            f"dbname='{cls.database}' user='{cls.db_user}' "
            f"password='{cls.db_user_pw}'"
        )

        connection = psycopg.connect(connect_string)
        cursor = connection.cursor()

        params = {"access_key": cls.access_key}
        forex_dict = {}
        try:
            res = requests.get(cls.forex_url, params=params)
            if res:
                forex_dict = res.json().get("quotes", {})

            else:
                logger.info(f"connection error: {cls.forex_url} {params}")
                return

        except requests.exceptions.ConnectionError:
            logger.info(f"connection error: {cls.forex_url} {params}")
            return

        if forex_dict:
            sql_string = (
                f"SELECT id, currency, usd_exchange_rate FROM {cls.table_currency} "
                f"ORDER BY currency;"
            )
            cursor.execute(sql_string)

            for currency in cursor.fetchall():
                usd_exchange_rate = forex_dict.get("USD" + currency[1], "")
                if usd_exchange_rate:
                    sql_string = (
                        f"UPDATE {cls.table_currency} SET "
                        f"usd_exchange_rate='{usd_exchange_rate}' "
                        f"WHERE currency='{currency[1]}';"
                    )
                    cursor.execute(sql_string)

                    sql_string = (
                        f"SELECT id, usd_exchange_rate_low, usd_exchange_rate_high, usd_exchange_rate "
                        f"FROM {cls.table_currencyhistory} "
                        f"WHERE currency_id = {currency[0]} and currency_date = '{utc_date}';"
                    )
                    cursor.execute(sql_string)

                    if not (vals := cursor.fetchone()):
                        sql_string = (
                            f"INSERT INTO {cls.table_currencyhistory} ( "
                            f"currency_id, "
                            f"currency_date, "
                            f"usd_exchange_rate_low, "
                            f"usd_exchange_rate_high, "
                            f"usd_exchange_rate) "
                            f"VALUES (%s, %s, %s, %s, %s);"
                        )
                        cursor.execute(
                            sql_string,
                            (
                                currency[0],
                                utc_date,
                                usd_exchange_rate,
                                usd_exchange_rate,
                                usd_exchange_rate,
                            ),
                        )
                    else:
                        if float(usd_exchange_rate) < float(vals[1]):
                            usd_exchange_rate_low = usd_exchange_rate
                        else:
                            usd_exchange_rate_low = vals[1]

                        if float(usd_exchange_rate) > float(vals[2]):
                            usd_exchange_rate_high = usd_exchange_rate
                        else:
                            usd_exchange_rate_high = vals[2]

                        sql_string = (
                            f"UPDATE {cls.table_currencyhistory} SET "
                            f"usd_exchange_rate = %s, "
                            f"usd_exchange_rate_low = %s, "
                            f"usd_exchange_rate_high = %s "
                            f"WHERE id = %s;"
                        )
                        cursor.execute(
                            sql_string,
                            (
                                usd_exchange_rate,
                                usd_exchange_rate_low,
                                usd_exchange_rate_high,
                                vals[0],
                            ),
                        )

        else:
            logger.info(f"unable to get currency data for {cls.forex_url} {params}")

        connection.commit()
        cursor.close()
        connection.close()


def main():
    uc = UpdateCurrencies()
    uc.update_currencies()


if __name__ == "__main__":
    main()
