"""  module to handle stock. It has two classes:
        - StockTools:
          handling initiating the stock database and extracting and creating
          portfolios based on data in excel files
          Methods:
            - exchanges_and_currencies
            - symbols
            - create_portfolios
            - extract_portfolios

        - TradingData:
          method for parsing quotes, extracting symbols and communicates
          with stock providing API of Financial Modeling Prep. If a stock
          symbol is not found in Financial Modeling Prep it will try to get
          the information from an alternative API, defined in another module
          Methods:
            - setup
            - get_schema
            - get_stock_trade_info
            - get_cash_trade_info
            - get_stock_trade_info_on_date
            - get_stock_intraday_info
            - get_stock_history_info
            - parse_stock_quote
            - get_portfolio_stock_info
            - calculate_stocks_value
"""

import decimal
from decimal import Decimal as d
import datetime
from collections import namedtuple
import pandas as pd
from decouple import config
import requests
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.tradetime import tradetime_fromtimestamp, tradetime_fromstring
from howdimain.utils.min_max import get_min, get_max
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED, URL_FMP
from stock.models import (
    Person,
    Exchange,
    Currency,
    Stock,
    Portfolio,
    StockSelection,
)
from stock.module_marketstack import (
    get_stock_marketstack,
    get_intraday_marketstack,
    get_history_marketstack,
)
from stock.module_alpha_vantage import (
    get_stock_alpha_vantage,
    get_intraday_alpha_vantage,
    get_history_alpha_vantage,
)


logger = Logger.getlogger()


class StockTools:
    """methods to read stocks and populate the database"""

    @staticmethod
    def exchanges_and_currencies(filename: str):
        exchanges_df = pd.read_excel(filename, index_col=0)

        db_exchanges = [exchange.mic for exchange in Exchange.objects.all()]
        db_currencies = [currency.currency for currency in Currency.objects.all()]

        for index, row in exchanges_df.iterrows():
            if pd.isnull(row["currency"]):
                currency = "N/A"

            else:
                currency = row["currency"]

            if currency not in db_currencies:
                try:
                    Currency.objects.create(currency=currency)
                    db_currencies.append(row.currency)
                    print(f"processing {index:4}: adding currency: {currency}")

                except IntegrityError:
                    print(
                        f"processing {index:4}: currency: {currency} already processed"
                    )

            # ignore if exchange already exist
            if row["mic"] in db_exchanges:
                continue

            try:
                Exchange.objects.create(
                    mic=row["mic"],
                    ric=row["ric"],
                    name=row["name"],
                    acronym=row["acronym"],
                    country_code=row["country_code"],
                    city=row["city"],
                    website=row["website"],
                    timezone=row["timezone"],
                    currency=Currency.objects.get(currency=currency),
                )
                db_exchanges.append(row.mic)
                print(f'processing {index:4}: adding exchange: {row["name"]}')

            except IntegrityError:
                print(
                    f'processing {index:4}: integrity error for exchange: {row["name"]}'
                )

    @staticmethod
    def symbols(filename: str):
        stocks_df = pd.read_excel(filename, index_col=0, keep_default_na=False)

        for index, row in stocks_df.iterrows():
            symbol_ric = row["symbol"]
            if len(symbol_ric) > 20:
                continue

            symbol_ric_parts = symbol_ric.split(".")
            ric = symbol_ric_parts[-1] if len(symbol_ric) > 1 else None
            if symbol_ric[0] == "^":
                exchange_mic = "INDEX"

            else:
                exchange_mic = row["exchange_mic"]

            if not exchange_mic or pd.isnull(exchange_mic):
                try:
                    exchange_mic = Exchange.objects.get(ric=ric).mic

                except Exchange.DoesNotExist:
                    exchange_mic = "XNAS"

            symbol_mic = ".".join([symbol_ric_parts[0], exchange_mic])
            if len(symbol_mic) > 20:
                continue

            try:
                Stock.objects.create(
                    symbol=symbol_mic,
                    symbol_ric=symbol_ric,
                    company=str(row["name"])[0:75],
                    exchange=Exchange.objects.get(mic=exchange_mic),
                    currency=Exchange.objects.get(mic=exchange_mic).currency,
                    type=row["type"][0:10],
                )
                # print(f'processing {index:4}: symbol {row["symbol"]} - {row["name"]}')
                logger.info(
                    f'processing {index:4}: symbol {row["symbol"]} - {row["name"]}'
                )

            except IntegrityError:
                print(
                    f'processing {index:4}: already in database, symbol: {row["symbol"]}'
                )
                logger.info(
                    f'processing {index:4}: already in database, symbol: {row["symbol"]}'
                )

    @staticmethod
    def create_portfolios(filename: str, ric=False):
        portfolios_df = pd.read_excel(filename, index_col=0)

        for index, row in portfolios_df.iterrows():
            try:
                user = Person.objects.get(username=row["username"])
            except Person.DoesNotExist:
                continue

            try:
                if ric:
                    stock = Stock.objects.get(symbol_ric=row["symbol"])

                else:
                    stock = Stock.objects.get(symbol=row["symbol"])

            except Stock.DoesNotExist:
                continue

            try:
                Portfolio.objects.create(
                    portfolio_name=row["portfolio_name"],
                    user=user,
                )

            except IntegrityError:
                pass

            try:
                StockSelection.objects.create(
                    stock=stock,
                    quantity=row["quantity"],
                    portfolio=Portfolio.objects.get(
                        portfolio_name=row["portfolio_name"],
                        user=user,
                    ),
                )
                print(
                    f'processing {index:4}: add {row["symbol"]} '
                    f'to portfolio {row["portfolio_name"]} '
                    f'for user {row["username"]}'
                )

            except IntegrityError:
                print(
                    f'processing {index:4}: unable to add {row["symbol"]}'
                    f'to portfolio {row["portfolio_name"]} '
                    f'for user {row["username"]}'
                )

    @staticmethod
    def extract_portfolios(user_portfolios_filename: str):
        users = Person.objects.all()

        portfolios_dict = {
            "username": [],
            "portfolio_name": [],
            "symbol": [],
            "company": [],
            "quantity": [],
        }

        for user in users:
            portfolios = Portfolio.objects.filter(user=user)
            for portfolio in portfolios:
                stocks = StockSelection.objects.filter(portfolio=portfolio)
                for stock in stocks:
                    print(
                        f"user: {user.username}, "
                        f"portfolio: {portfolio.portfolio_name}, "
                        f"symbol: {stock.stock.symbol}, "
                        f"company: {stock.stock.company}, "
                        f"quantity: {stock.quantity}"
                    )
                    portfolios_dict["username"].append(user.username)
                    portfolios_dict["portfolio_name"].append(portfolio.portfolio_name)
                    portfolios_dict["symbol"].append(stock.stock.symbol)
                    portfolios_dict["company"].append(stock.stock.company)
                    portfolios_dict["quantity"].append(stock.quantity)

        portfolios_df = pd.DataFrame(portfolios_dict)
        portfolios_df.to_excel(user_portfolios_filename)


class TradingData:
    """Methods to handle trading data from various sources
    based on FMP and as fall back to Marketstack
    """

    "try-except introduced for tests when no DB has yet been created"
    try:
        cash_stocks = []
        if Exchange.objects.filter(mic="CASH").exists():
            cash_stocks = [
                symbol.symbol_ric
                for symbol in Exchange.objects.get(mic="CASH").stocks.all()
            ]
    except Exception as error:
        cash_stocks = ["EUR.CASH", "USD.CASH"]
        logger.info(f"{error=}, {cash_stocks=}")

    @classmethod
    def setup(cls):
        cls.api_token = config("API_token")

        # cls.stock_url = 'https://financialmodelingprep.com/api/v3/quote-symex-private-endpoint/'
        cls.stock_url = "https://financialmodelingprep.com/api/v3/quote/"
        cls.intraday_url = "https://financialmodelingprep.com/api/v3/historical-chart/"
        cls.history_url = (
            "https://financialmodelingprep.com/api/v3/historical-price-full/"
        )
        cls.news_url = "https://financialmodelingprep.com/api/v3/stock_news"
        cls.press_url = "https://financialmodelingprep.com/api/v3/press-releases/"
        cls.time_interval = "5min"
        cls.data_provider_url = URL_FMP

    @staticmethod
    def get_schema(_format):
        return [
            {
                "name": "Date",
                "type": "date",
                "format": _format,
            },
            {
                "name": "open",
                "type": "number",
            },
            {
                "name": "close",
                "type": "number",
            },
            {
                "name": "low",
                "type": "number",
            },
            {
                "name": "high",
                "type": "number",
            },
            {
                "name": "volume",
                "type": "number",
            },
        ]

    @classmethod
    def get_stock_trade_info(cls, stock_symbols: list) -> list:
        """return the stock trade info as a dict retrieved from url json, key data."""
        for cash_symbol in cls.cash_stocks:
            if cash_symbol in stock_symbols:
                stock_symbols.remove(cash_symbol)

        symbols = ",".join(stock_symbols).upper()
        stock_url = cls.stock_url + symbols
        params = {"apikey": cls.api_token}

        stock_list = []
        if stock_symbols:
            try:
                res = requests.get(stock_url, params=params)
                if res and res.status_code == 200:
                    stock_list = res.json()
                else:
                    pass

            except requests.exceptions.ConnectionError:
                logger.info(f"connection error: {cls.stock_url} {symbols} {params}")

        else:
            pass

        if len(stock_symbols) > MAX_SYMBOLS_ALLOWED:
            logger.warning(
                f"number of symbols exceed " f"maximum of {MAX_SYMBOLS_ALLOWED}"
            )
        stock_info = []
        for quote in stock_list:
            stock_dict = {}
            # get currency and exchange info from the database if it does not exist
            # skip this quote
            try:
                stock = Stock.objects.get(symbol_ric=quote["symbol"])

            except Stock.DoesNotExist:
                continue

            stock_dict["currency"] = stock.currency.currency
            stock_dict["exchange_mic"] = stock.exchange.mic
            stock_dict["name"] = stock.company
            stock_dict["symbol"] = quote.get("symbol")
            stock_dict["open"] = quote.get("open")
            stock_dict["day_high"] = quote.get("dayHigh")
            stock_dict["day_low"] = quote.get("dayLow")
            stock_dict["price"] = quote.get("price")
            stock_dict["volume"] = quote.get("volume")
            stock_dict["close_yesterday"] = quote.get("previousClose")
            stock_dict["day_change"] = quote.get("change")
            stock_dict["change_pct"] = quote.get("changesPercentage")
            stock_dict["last_trade_time"] = tradetime_fromtimestamp(
                quote.get("timestamp"), stock_dict["exchange_mic"]
            )

            stock_info.append(stock_dict)

        # try to get missing symbols through marketstack
        if stock_info:
            captured_symbols = [s.get("symbol", "") for s in stock_info]
        else:
            captured_symbols = []

        missing_symbols = [s for s in stock_symbols if s not in captured_symbols]

        if missing_symbols:
            stock_info += get_stock_marketstack(missing_symbols)

        # try to get missing symbols through alpha vantage
        if stock_info:
            captured_symbols = [s.get("symbol", "") for s in stock_info]
        else:
            captured_symbols = []

        missing_symbols = [s for s in stock_symbols if s not in captured_symbols]

        if missing_symbols:
            stock_info += get_stock_alpha_vantage(missing_symbols)

        return stock_info

    @staticmethod
    def get_cash_trade_info(cash_list: list) -> list:
        cash_info = []
        for symbol in cash_list:
            cash_dict = {}
            try:
                cash_stock = Stock.objects.get(symbol_ric=symbol)

            except Stock.DoesNotExist:
                continue

            cash_dict["currency"] = cash_stock.currency.currency
            cash_dict["exchange_mic"] = cash_stock.exchange.mic
            cash_dict["name"] = cash_stock.company
            cash_dict["symbol"] = symbol
            cash_dict["open"] = 1.0
            cash_dict["day_high"] = 1.0
            cash_dict["day_low"] = 1.0
            cash_dict["price"] = 1.0
            cash_dict["volume"] = 1.0
            cash_dict["close_yesterday"] = 1.0
            cash_dict["day_change"] = 0.0
            cash_dict["change_pct"] = 0.0
            cash_dict["last_trade_time"] = tradetime_fromstring(
                "", cash_dict["exchange_mic"]
            )
            cash_info.append(cash_dict)

        return cash_info

    @staticmethod
    def get_stock_trade_info_on_date(trading_date: str, symbols: list) -> list:
        stock_info = []
        for symbol in symbols:
            stock_dict = {}
            stock = Stock.objects.get(symbol_ric=symbol)
            info = stock.history.filter(last_trading_time__date=trading_date).last()
            stock_dict["currency"] = stock.currency.currency
            stock_dict["exchange_mic"] = stock.exchange.mic
            stock_dict["name"] = stock.company
            stock_dict["symbol"] = stock.symbol_ric
            stock_dict["open"] = info.open
            stock_dict["day_high"] = info.day_high
            stock_dict["day_low"] = info.day_low
            stock_dict["price"] = info.latest_price
            stock_dict["volume"] = info.volume
            stock_dict["close_yesterday"] = info.close_yesterday
            stock_dict["day_change"] = info.day_change
            stock_dict["change_pct"] = info.change_pct
            stock_dict["last_trade_time"] = info.last_trading_time
            stock_info.append(stock_dict)

        return stock_info

    @classmethod
    def get_stock_intraday_info(cls, stock_symbol: str) -> list:
        """return stock intraday info as a dict retrieved from url json,
        key 'intraday'
        """
        if stock_symbol.upper() in cls.cash_stocks:
            return []

        intraday_url = cls.intraday_url + "/".join([cls.time_interval, stock_symbol])
        params = {"apikey": cls.api_token}
        _intraday_trades = []
        try:
            res = requests.get(intraday_url, params=params)
            if res:
                _intraday_trades = res.json()
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f"connection error: {intraday_url} {stock_symbol} {params}")

        # if there is intraday info, convert date string and provide time and
        # create list of trade_info tuples
        trade_tuple = namedtuple("trade_tuple", "date open close low high volume")
        intraday_trades = []
        min_low = None
        max_high = None
        if _intraday_trades:
            date_trade = datetime.datetime.strptime(
                _intraday_trades[0].get("date"), "%Y-%m-%d %H:%M:%S"
            ).date()

            for i, _trade in enumerate(_intraday_trades):
                _tradetime = datetime.datetime.strptime(
                    _trade.get("date"), "%Y-%m-%d %H:%M:%S"
                )
                if _tradetime.date() != date_trade:
                    break

                # adjust cumulative volumes
                try:
                    volume = _trade.get("volume") - _intraday_trades[i + 1].get(
                        "volume"
                    )
                    if volume < 0:
                        volume = 0
                except IndexError:
                    volume = 0

                intraday_trades.append(
                    trade_tuple(
                        date=_tradetime,
                        open=_trade.get("open"),
                        close=_trade.get("close"),
                        low=_trade.get("low"),
                        high=_trade.get("high"),
                        volume=volume,
                    )
                )
                min_low = get_min(_trade.get("low"), min_low)
                max_high = get_max(_trade.get("high"), max_high)

            intraday_trades = sorted(intraday_trades, key=lambda k: k.date)

            # add start and end time
            initial_open = intraday_trades[0].open
            last_close = intraday_trades[-1].close
            start_time = intraday_trades[0].date.strftime("%Y-%m-%d") + " 08:00:00"
            intraday_trades.insert(
                0,
                trade_tuple(
                    date=datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
                    open=None,
                    close=None,
                    low=None,
                    high=None,
                    volume=None,
                ),
            )
            end_time = intraday_trades[-1].date.strftime("%Y-%m-%d") + " 18:00:00"
            intraday_trades.append(
                trade_tuple(
                    date=datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
                    open=initial_open,
                    close=last_close,
                    low=min_low,
                    high=max_high,
                    volume=None,
                )
            )

        else:
            # if not succeeded try with fallback site on marketstack
            intraday_trades = get_intraday_marketstack(stock_symbol)

            # or (last resort) try alpha vantage
            if not intraday_trades:
                intraday_trades = get_intraday_alpha_vantage(stock_symbol)

        return intraday_trades

    @classmethod
    def get_stock_history_info(cls, stock_symbol: str, period=None) -> list:
        """return stock history info as a dict retrieved from url json,
        key 'history'
        """
        if stock_symbol.upper() in cls.cash_stocks:
            return []

        history_url = cls.history_url + stock_symbol
        params = {"apikey": cls.api_token}

        _daily_trades = []
        try:
            res = requests.get(history_url, params=params)
            if res:
                _daily_trades = res.json().get("historical", [])
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f"connection error: {history_url} {stock_symbol} {params}")

        # if there is history info, convert date string and provide date and
        # create list of trade_info tuples
        trade_tuple = namedtuple("trade_tuple", "date open close low high volume")
        daily_trades = []
        if _daily_trades:
            for trade in _daily_trades:
                daily_trades.append(
                    trade_tuple(
                        date=datetime.datetime.strptime(trade.get("date"), "%Y-%m-%d"),
                        open=trade.get("open"),
                        close=trade.get("close"),
                        low=trade.get("low"),
                        high=trade.get("high"),
                        volume=trade.get("volume"),
                    )
                )

        else:
            # if not succeeded try with fallback site on marketstack
            daily_trades = get_history_marketstack(stock_symbol, period)

            # or (last resort) try alpha vantage
            if not daily_trades:
                daily_trades = get_history_alpha_vantage(stock_symbol)

        return daily_trades

    @classmethod
    def parse_stock_quote(cls, stock_quote: str, markets=None) -> list:
        """parse stock names searching the worldtradingdata database in three
        passes: 1) is the stock name the actual ticker symbol,
        2) if not does it start with the stock_name or 3) does the company
        name contain the stock_name.

        arguments: string with stock names, like: 'Wolters, AAPL, 'msft'
        returns: list of ticker symbols

        Stock is Django model containing stock information
        """
        if markets is None:
            markets = []

        #  use set to avoid duplicates and extract stock names from the string
        stock_symbols = set()
        stock_names = [stock.strip() for stock in stock_quote.split(",")]

        def add_stock_symbol_if_valid(stock_symbol):
            """only add if stock_symbol is listed on one of the markets or
            markets is empty
            """
            if (
                markets == []
                or Stock.objects.filter(symbol_ric=stock_symbol).first().exchange.mic
                in markets
            ):
                if not stock_symbol.upper() in cls.cash_stocks:
                    stock_symbols.add(stock_symbol)
            else:
                pass

        for stock_name in stock_names:
            #  check is stock name is not empty
            if stock_name == "":
                continue

            #  check if stock_name is the actual symbol
            if Stock.objects.filter(symbol_ric=stock_name.upper()):
                add_stock_symbol_if_valid(stock_name.upper())
                continue

            #  add symbols if the company starts with stock_name (titled)
            for stock in Stock.objects.filter(company__startswith=stock_name.title()):
                add_stock_symbol_if_valid(stock.symbol_ric)

            #  add symbols if the company contains the stock_name (exact match)
            for stock in Stock.objects.filter(company__icontains=stock_name):
                add_stock_symbol_if_valid(stock.symbol_ric)

        return list(stock_symbols)

    @classmethod
    def get_portfolio_stock_info(
        cls, portfolio: Portfolio, base_currency_name: str, trading_date: str = None
    ) -> list:
        if trading_date:
            symbols_quantities = portfolio.get_stock_on_date(trading_date)

        else:
            symbols_quantities = portfolio.get_stock()

        list_symbols = list(symbols_quantities.keys())
        if trading_date:
            stock_trade_info = cls.get_stock_trade_info_on_date(
                trading_date, list_symbols
            )
        else:
            # split cash components
            cash_symbols = []
            for cash_stock in cls.cash_stocks:
                if cash_stock in list_symbols:
                    list_symbols.remove(cash_stock)
                    cash_symbols.append(cash_stock)

            stock_trade_info = cls.get_stock_trade_info(
                list_symbols[0:MAX_SYMBOLS_ALLOWED]
            )
            stock_trade_info += cls.get_stock_trade_info(
                list_symbols[MAX_SYMBOLS_ALLOWED : 2 * MAX_SYMBOLS_ALLOWED]
            )
            if len(list_symbols) > 2 * MAX_SYMBOLS_ALLOWED:
                logger.warning(
                    f"number of symbols in portfolio exceed "
                    f"maximum of {2 * MAX_SYMBOLS_ALLOWED}"
                )
            stock_trade_info += cls.get_cash_trade_info(cash_symbols)

        stock_info = []
        for stock in stock_trade_info:
            stock["quantity"] = symbols_quantities[stock["symbol"]]

            exchange_rate = Currency.objects.get(
                currency=stock["currency"]
            ).get_exchangerate_on_date(trading_date)

            try:
                value = d(stock["quantity"]) * d(stock["price"]) / d(exchange_rate)
                value_change = (
                    d(stock["quantity"]) * d(stock["day_change"]) / d(exchange_rate)
                )

            except (NameError, decimal.InvalidOperation):
                value = "n/a"
                value_change = "n/a"

            if base_currency_name == "USD" or value == "n/a":
                pass

            elif base_currency_name == "EUR":
                exchange_rate_euro = Currency.objects.get(
                    currency="EUR"
                ).get_exchangerate_on_date(trading_date)
                value *= d(exchange_rate_euro)
                value_change *= d(exchange_rate_euro)

            else:
                logger.warning(f"Invalid base currency {base_currency_name}")

            stock["value"] = str(value)
            stock["value_change"] = str(value_change)

            stock_info.append(stock)

        return stock_info

    @classmethod
    def calculate_stocks_value(cls, stocks):
        total_value = d("0")
        total_value_change = d("0")
        for stock in stocks:
            try:
                total_value += d(stock["value"])

            except decimal.InvalidOperation:
                pass

            try:
                total_value_change += d(stock["value_change"])

            except decimal.InvalidOperation:
                pass

        return str(total_value), str(total_value_change)

    @staticmethod
    def get_usd_euro_exchangerate(currency: str, trading_date: str = None):
        exchange_rate = float(
            Currency.objects.get(currency="EUR").get_exchangerate_on_date(trading_date)
        )
        if currency == "USD":
            return f"USD/EUR: {exchange_rate:.4f}"

        elif currency == "EUR":
            return f"EUR/USD: { 1.0 / exchange_rate:.4f}"

        else:
            assert (
                False
            ), f"invalid currency parameter: {currency}, should be USD or EUR"

    def get_stock_press(cls, stock_symbol: str, limit: int = 10) -> list:
        press_news = []
        press_url = cls.press_url + stock_symbol.upper()
        params = {"limit": limit, "apikey": cls.api_token}
        try:
            res = requests.get(press_url, params=params)
            if res and res.status_code == 200:
                press_news = res.json()
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f"connection error: {press_url} {params}")

        return press_news

    def get_stock_news(cls, stock_symbol: str, limit: int = 10) -> list:
        stock_news = []
        params = {
            "tickers": stock_symbol.upper(),
            "limit": limit,
            "apikey": cls.api_token,
        }
        try:
            res = requests.get(cls.news_url, params=params)
            if res and res.status_code == 200:
                stock_news = res.json()
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f"connection error: {cls.news_url} {params}")

        return stock_news

    @staticmethod
    def get_company_name(stock_symbol):
        try:
            return Stock.objects.get(symbol_ric=stock_symbol).company

        except Stock.DoesNotExist:
            return ""
