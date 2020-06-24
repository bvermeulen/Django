import decimal
from decimal import Decimal as d
import datetime
import csv
from collections import namedtuple
from decouple import config
import requests
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.last_tradetime import last_trade_time
from howdimain.utils.min_max import get_min, get_max
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED, URL_FMP
from stock.models import Exchange, Currency, Stock, Portfolio, StockSelection
from stock.stock_lists import stock_lists
from stock.module_alpha_vantage import (
    get_stock_alpha_vantage, get_intraday_alpha_vantage, get_history_alpha_vantage,
)

logger = Logger.getlogger()

class PopulateStock:

    @classmethod
    def read_csv(cls, filename):
        cls.stock_data = []
        with open(filename) as csv_file:
            _stock_data = csv.reader(csv_file, delimiter=",")
            # skip the header
            next(_stock_data, None)
            for row in _stock_data:
                cls.stock_data.append(row)

    @classmethod
    def exchanges_and_currencies(cls,):
        db_exchanges = [exchange.exchange_short for exchange in Exchange.objects.all()]
        db_currencies = [currency.currency for currency in Currency.objects.all()]

        for row in cls.stock_data:
            if row[2] == '':
                currency = 'N/A'

            else:
                currency = row[2]

            if row[4] in db_exchanges:
                pass

            else:
                try:
                    if row[3] == '':
                        exchange_long = row[4][5:] + ' INDEX'

                    else:
                        exchange_long = row[3]

                    Exchange.objects.create(
                        exchange_long=exchange_long,
                        exchange_short=row[4],
                        time_zone_name=row[5]
                    )
                    db_exchanges.append(exchange_long)
                    print(f'adding exchange: {exchange_long}')

                except IntegrityError:
                    pass

            if row[2] in db_currencies:
                continue

            else:
                try:
                    Currency.objects.create(currency=currency)
                    db_currencies.append(currency)
                    print(f'adding currency: {currency}')

                except IntegrityError:
                    pass

    @classmethod
    def symbols(cls,):
        for i, row in enumerate(cls.stock_data):
            if row[2] == '':
                currency = 'N/A'

            else:
                currency = row[2]

            if row[0]:
                try:
                    _ = Stock.objects.create(
                        symbol=row[0],
                        company=row[1][0:75],
                        currency=Currency.objects.get(currency=currency),
                        exchange=Exchange.objects.get(exchange_short=row[4]),
                        )
                    print(f'processing row {i}, stock {row[0]} - {row[1]}')
                    logger.info(f'processing row {i}, stock {row[0]} - {row[1]}')

                except IntegrityError:
                    pass
                    # print(f'already in database, stock: {row[1]}')
                    # logger.info(f'already in database, stock: {row[1]}')

    @classmethod
    def create_default_portfolios(cls,):
        default = User.objects.get(username='default_user')

        portfolio = Portfolio.objects.create(portfolio_name='Techno', user=default)
        for stock_symbol in stock_lists.get('TECH'):
            stock = Stock.objects.get(symbol=stock_symbol)
            _ = StockSelection.objects.create(
                stock=stock, quantity=1, portfolio=portfolio)

        portfolio = Portfolio.objects.create(
            portfolio_name='AEX', user=default)
        for stock_symbol in stock_lists.get('AEX'):
            stock = Stock.objects.get(symbol=stock_symbol)
            _ = StockSelection.objects.create(
                stock=stock, quantity=1, portfolio=portfolio)

        portfolio = Portfolio.objects.create(portfolio_name='Dow Jones', user=default)
        for stock_symbol in stock_lists.get('DOW'):
            print(stock_symbol)
            stock = Stock.objects.get(symbol=stock_symbol)
            _ = StockSelection.objects.create(
                stock=stock, quantity=1, portfolio=portfolio)

    @classmethod
    def compare_and_clean_database_with_wtd(cls, dummy=True):
        ''' cleans database by comparing to wrd stock listing
            to affect database dummy must be set to False
        '''

        database_symbols = [
            stock.symbol for stock in Stock.objects.all()]
        database_exchanges = [
            exchange.exchange_short for exchange in Exchange.objects.all()]
        database_currencies = [
            currency.currency for currency in Currency.objects.all()]

        wtd_symbols = {stock[0] for stock in cls.stock_data}
        wtd_exchanges = {stock[4] for stock in cls.stock_data}
        wtd_currencies = {stock[2] for stock in cls.stock_data}

        print('clearing stocks')
        logger.info('clearing stocks')
        for symbol in database_symbols:
            if symbol not in wtd_symbols:
                print(f'delete stock {symbol}')
                logger.info(f'delete stock {symbol}')
                if not dummy:
                    Stock.objects.get(symbol=symbol).delete()

        print('clearing exchanges')
        logger.info('clearing exchanges')
        for exchange in database_exchanges:
            if exchange not in wtd_exchanges:
                print(f'delete exchange {exchange}')
                logger.info(f'delete exchange {exchange}')
                if not dummy:
                    Exchange.objects.get(exchange_short=exchange).delete()

        print('clearing currencies')
        logger.info('clearing currencies')
        for currency in database_currencies:
            if currency not in wtd_currencies and currency != 'N/A':
                print(f'delete currency {currency}')
                logger.info(f'delete currency {currency}')
                if not dummy:
                    Currency.objects.get(currency=currency).delete()

class TradingData:
    ''' methods to handle trading data from various sources
        based on FMP and as fall back Alpha Vantage
    '''
    @classmethod
    def setup(cls,):
        cls.api_token = config('API_token')
        cls.stock_url = 'https://financialmodelingprep.com/api/v3/quote-symex-private-endpoint/'  #pylint: disable=line-too-long
        cls.intraday_url = 'https://financialmodelingprep.com/api/v3/historical-chart/'           #pylint: disable=line-too-long
        cls.history_url = 'https://financialmodelingprep.com/api/v3/historical-price-full/'       #pylint: disable=line-too-long
        cls.time_interval = '5min'

        cls.data_provider_url = URL_FMP

    @staticmethod
    def get_schema(_format):
        return [{'name': 'Date',
                 'type': 'date',
                 'format': _format,
                },
                {'name': 'open',
                 'type': 'number',
                },
                {'name': 'close',
                 'type': 'number',
                },
                {'name': 'low',
                 'type': 'number',
                },
                {'name': 'high',
                 'type': 'number',
                },
                {'name': 'volume',
                 'type': 'number',
                },]

    @classmethod
    def get_stock_trade_info(cls, stock_symbols: list) -> list:
        ''' return the stock trade info as a dict retrieved from url json, key 'data'
        '''
        symbols = ','.join(stock_symbols).upper()
        stock_url = cls.stock_url + symbols
        params = {'apikey': cls.api_token}

        stock_list = []
        if stock_symbols:
            try:
                res = requests.get(stock_url, params=params)
                if res and res.status_code == 200:
                    stock_list = res.json()
                else:
                    pass

            except requests.exceptions.ConnectionError:
                logger.info(f'connection error: {cls.stock_url} {symbols} {params}')

        else:
            pass

        if len(stock_symbols) > MAX_SYMBOLS_ALLOWED:
            logger.warning(f'number of symbols exceed '
                           f'maximum of {MAX_SYMBOLS_ALLOWED}')
        stock_info = []
        for quote in stock_list:

            stock_dict = {}
            # get currency and exchange info from the database if it does not exist
            # skip this quote
            try:
                stock_db = Stock.objects.get(symbol=quote['symbol'])

            except Stock.DoesNotExist:
                continue

            stock_dict['currency'] = stock_db.currency.currency
            stock_dict['stock_exchange_short'] = stock_db.exchange.exchange_short

            stock_dict['symbol'] = quote.get('symbol')
            stock_dict['name'] = quote.get('name')
            stock_dict['open'] = quote.get('open')
            stock_dict['day_high'] = quote.get('dayHigh')
            stock_dict['day_low'] = quote.get('dayLow')
            stock_dict['price'] = quote.get('price')
            stock_dict['volume'] = quote.get('volume')
            stock_dict['close_yesterday'] = quote.get('previousClose')
            stock_dict['day_change'] = quote.get('change')
            stock_dict['change_pct'] = quote.get('changesPercentage')
            stock_dict['last_trade_time'] = last_trade_time(
                quote.get('lastTradeTimeStamp'), stock_dict['stock_exchange_short']
            )

            stock_info.append(stock_dict)

        # try to get missing symbols through alpha_vantage
        if stock_info:
            captured_symbols = [s.get('symbol', '') for s in stock_info]
        else:
            captured_symbols = []

        missing_symbols = [s for s in stock_symbols if s not in captured_symbols]

        if missing_symbols:
            # TODO remove print statement after DEBUGGING
            print(f'missing symbols: {missing_symbols}')
            stock_info += get_stock_alpha_vantage(missing_symbols)

        return stock_info

    @classmethod
    def get_stock_intraday_info(cls, stock_symbol: str) -> list:
        '''  return stock intraday info as a dict retrieved from url json,
             key 'intraday'
        '''
        intraday_url = cls.intraday_url + '/'.join([cls.time_interval, stock_symbol])
        params = {'apikey': cls.api_token}
        _intraday_trades = []
        try:
            res = requests.get(intraday_url, params=params)
            if res:
                _intraday_trades = res.json()
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {intraday_url} {stock_symbol} {params}')

        # if there is intraday info, convert date string and provide time and
        # create list of trade_info tuples
        trade_tuple = namedtuple('trade_tuple', 'date open close low high volume')
        intraday_trades = []
        min_low = None
        max_high = None
        if _intraday_trades:
            date_trade = datetime.datetime.strptime(
                _intraday_trades[0].get('date'), "%Y-%m-%d %H:%M:%S").date()

            for i, _trade in enumerate(_intraday_trades):
                _tradetime = datetime.datetime.strptime(
                    _trade.get('date'), "%Y-%m-%d %H:%M:%S")
                if _tradetime.date() != date_trade:
                    break

                # adjust cumulative volumes
                try:
                    volume = _trade.get('volume') - _intraday_trades[i+1].get('volume')
                    if volume < 0:
                        volume = 0
                except IndexError:
                    volume = 0

                intraday_trades.append(
                    trade_tuple(
                        date=_tradetime,
                        open=_trade.get('open'),
                        close=_trade.get('close'),
                        low=_trade.get('low'),
                        high=_trade.get('high'),
                        volume=volume,
                    )
                )
                min_low = get_min(_trade.get('low'), min_low)
                max_high = get_max(_trade.get('high'), max_high)

            intraday_trades = sorted(intraday_trades, key=lambda k: k.date)

            # add start and end time
            initial_open = intraday_trades[0].open
            last_close = intraday_trades[-1].close
            start_time = intraday_trades[0].date.strftime("%Y-%m-%d") + ' 08:00:00'
            intraday_trades.insert(
                0, trade_tuple(date=datetime.datetime.strptime(
                    start_time, "%Y-%m-%d %H:%M:%S"),
                               open=None,
                               close=None,
                               low=None,
                               high=None,
                               volume=None)
            )
            end_time = intraday_trades[-1].date.strftime("%Y-%m-%d") + ' 18:00:00'
            intraday_trades.append(
                trade_tuple(date=datetime.datetime.strptime(
                    end_time, "%Y-%m-%d %H:%M:%S"),
                            open=initial_open,
                            close=last_close,
                            low=min_low,
                            high=max_high, volume=None,)
            )

        else:
            # if not succeeded try with fallback site on alpha vantage
            intraday_trades = get_intraday_alpha_vantage(stock_symbol)
            # TODO remove after debugging
            print(f'going to Alpha Vantage to get intraday trade for {stock_symbol}')

        if not intraday_trades:
            logger.info(f'unable to get intraday stock data for '
                        f'{cls.history_url} {stock_symbol} {params}')

        return intraday_trades

    @classmethod
    def get_stock_history_info(cls, stock_symbol: str) -> list:
        '''  return stock history info as a dict retrieved from url json,
             key 'history'
        '''
        history_url = cls.history_url + stock_symbol
        params = {'apikey': cls.api_token}

        _daily_trades = []
        try:
            res = requests.get(history_url, params=params)
            if res:
                _daily_trades = res.json().get('history', [])
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {history_url} {stock_symbol} {params}')

        # if there is history info, convert date string and provide date and
        # create list of trade_info tuples
        trade_tuple = namedtuple('trade_tuple', 'date open close low high volume')
        daily_trades = []
        if _daily_trades:
            for trade in _daily_trades:
                daily_trades.append(
                    trade_tuple(
                        date=datetime.datetime.strptime(trade.get('date'), "%Y-%m-%d"),
                        open=trade.get('open'),
                        close=trade.get('close'),
                        low=trade.get('low'),
                        high=trade.get('high'),
                        volume=trade.get('volume'),
                    )
                )

        else:
            # if not succeeded try with fallback site on alpha vantage
            daily_trades = get_history_alpha_vantage(stock_symbol)
            # TODO remove after debugging
            print(f'going to Alpha Vantage to get history trades for {stock_symbol}')

        if not daily_trades:
            logger.info(f'unable to get stock history data for '
                        f'{cls.history_url} {stock_symbol} {params}')

        return daily_trades

    @classmethod
    def parse_stock_name(cls, stock_string: str, markets=None):
        ''' parse stock names searching the worldtradingdata database in three
            passes: 1) is the stock name the actual ticker symbol,
            2) if not does it start with the stock_name or 3) does the company
            name contain the stock_name.

            arguments: string with stock names, like: 'Wolters, AAPL, 'msft'
            returns: list of ticker symbols

            Stock is Django model containing stock information
        '''
        if markets is None:
            markets = []

        #  use set to avoid duplicates and extract stock names from the string
        stock_symbols = set()
        stock_names = [stock.strip() for stock in stock_string.split(',')]

        def add_stock_symbol_if_valid(stock_symbol):
            '''  only add if stock_symbol is listed on one of the markets or
                 markets is empty
            '''
            if markets == [] or Stock.objects.filter(symbol=stock_symbol).\
                                    first().exchange.exchange_short in markets:
                stock_symbols.add(stock_symbol)
            else:
                pass

        for stock_name in stock_names:
            #  check is stock name is not empty
            if stock_name == '':
                continue

            #  check if stock_name is the actual symbol
            if Stock.objects.filter(symbol=stock_name.upper()):
                add_stock_symbol_if_valid(stock_name.upper())
                continue

            stock_query = Stock.objects.filter(company__startswith=stock_name.title())
            if stock_query:
                #  check if name of the company starts with stock_name (titled)
                for stock in stock_query:
                    stock_symbol = Stock.objects.get(symbol=stock.symbol).symbol
                    add_stock_symbol_if_valid(stock_symbol)

            else:
                #  check if name of the companay contains the stock_name (exact match)
                for stock in Stock.objects.filter(company__icontains=stock_name):
                    stock_symbol = Stock.objects.get(symbol=stock.symbol).symbol
                    add_stock_symbol_if_valid(stock_symbol)

        return list(stock_symbols)

    @classmethod
    def get_portfolio_stock_info(cls, portfolio, base_currency):
        symbols_quantities = {stock.stock.symbol: stock.quantity
                              for stock in portfolio.stocks.all()}
        list_symbols = list(symbols_quantities.keys())
        stock_trade_info = cls.get_stock_trade_info(
            list_symbols[0:MAX_SYMBOLS_ALLOWED])
        stock_trade_info += cls.get_stock_trade_info(
            list_symbols[MAX_SYMBOLS_ALLOWED:2*MAX_SYMBOLS_ALLOWED])

        if len(list_symbols) > 2 * MAX_SYMBOLS_ALLOWED:
            logger.warning(f'number of symbols in portfolio exceed '
                           f'maximum of {2 * MAX_SYMBOLS_ALLOWED}')

        exchange_rate_euro = Currency.objects.get(
            currency='EUR').usd_exchange_rate

        stock_info = []
        for stock in stock_trade_info:
            stock['quantity'] = symbols_quantities[stock['symbol']]

            exchange_rate = Currency.objects.get(
                currency=stock['currency']).usd_exchange_rate

            try:
                value = d(stock["quantity"]) * d(stock["price"]) / d(exchange_rate)
                value_change = (
                    d(stock["quantity"]) * d(stock["day_change"]) / d(exchange_rate))

            except (NameError, decimal.InvalidOperation):
                value = 'n/a'
                value_change = 'n/a'

            if base_currency == 'USD' or value == 'n/a':
                pass

            elif base_currency == 'EUR':
                value *= d(exchange_rate_euro)
                value_change *= d(exchange_rate_euro)

            else:
                logger.warning(f'Invalid base currency {base_currency}')

            stock['value'] = str(value)
            stock['value_change'] = str(value_change)

            stock_info.append(stock)

        return stock_info

    @classmethod
    def calculate_stocks_value(cls, stocks):
        total_value = d('0')
        total_value_change = d('0')
        for stock in stocks:
            try:
                total_value += d(stock['value'])

            except decimal.InvalidOperation:
                pass

            try:
                total_value_change += d(stock['value_change'])

            except decimal.InvalidOperation:
                pass

        return str(total_value), str(total_value_change)
