''' update currency is meant as a cron job to update the currencies in the database
    used in howdimain for table stock_currency. It is not using the Django ORM
    but directly with sql.
'''
from decouple import config
import requests
import psycopg2
from howdimain.utils.plogger import Logger

logformat = '%(asctime)s:%(levelname)s:%(message)s'
Logger.set_logger(config('LOG_FILE'), logformat, 'INFO')
logger = Logger.getlogger()

class UpdateCurrencies:
    host = 'localhost'
    db_port = config('DB_PORT')
    db_user = config('DB_USER')
    db_user_pw = config('DB_PASSWORD')
    database = config('DB_NAME')

    access_key = config('access_key_currency')
    forex_url = 'http://api.currencylayer.com/live'

    @classmethod
    def update_currencies(cls):
        logger.info(f'update currencies using {cls.forex_url}')

        connect_string = f'host=\'{cls.host}\' port=\'{cls.db_port}\' '\
                         f'dbname=\'{cls.database}\' user=\'{cls.db_user}\' '\
                         f'password=\'{cls.db_user_pw}\''

        connection = psycopg2.connect(connect_string)
        cursor = connection.cursor()

        params = {'access_key': cls.access_key}
        forex_dict = {}
        try:
            res = requests.get(cls.forex_url, params=params)
            if res:
                forex_dict = res.json().get('quotes', {})

            else:
                logger.info(f'connection error: {cls.forex_url} {params}')
                return

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {cls.forex_url} {params}')
            return

        if forex_dict:
            sql_string = ('SELECT currency, usd_exchange_rate FROM stock_currency '
                          ' ORDER BY currency;')
            cursor.execute(sql_string)

            for currency in cursor.fetchall():
                usd_exchange_rate = forex_dict.get('USD' + currency[0], '')
                if usd_exchange_rate:
                    sql_string = (f'UPDATE stock_currency SET '
                                  f'usd_exchange_rate=\'{usd_exchange_rate}\' WHERE '
                                  f'currency=\'{currency[0]}\';')

                    cursor.execute(sql_string)

        else:
            logger.info(f'unable to get currency data for {cls.forex_url} {params}')

        connection.commit()
        cursor.close()
        connection.close()


if __name__ == '__main__':
    uc = UpdateCurrencies()
    uc.update_currencies()
