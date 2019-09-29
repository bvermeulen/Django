from decimal import Decimal as d
import threading
import datetime
import time
import csv
from collections import namedtuple
from decouple import config
import requests
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.min_max import get_min, get_max
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED, UPDATE_INTERVAL
from .models import Exchange, Currency, Stock, Portfolio, StockSelection
from .stock_lists import stock_lists

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
        for i, row in enumerate(cls.stock_data):
            print(f'processing row {i}, stock {row[1]}')
            try:
                Exchange.objects.create(
                    exchange_long=row[3],
                    exchange_short=row[4],
                    time_zone_name=row[5]
                )
            except IntegrityError:
                pass

            try:
                Currency.objects.create(
                    currency=row[2]
                )
            except IntegrityError:
                pass

    @classmethod
    def symbols(cls,):
        for i, row in enumerate(cls.stock_data):
            try:
                _ = Stock.objects.create(
                    symbol=row[0],
                    company=row[1][0:75],
                    currency=Currency.objects.get(currency=row[2]),
                    exchange=Exchange.objects.get(exchange_short=row[4]),
                )
                print(f'processing row {i}, stock {row[1]}')
                logger.info(f'processing row {i}, stock {row[1]}')

            except IntegrityError:
                print(f'already in database, stock: {row[1]}')
                logger.info(f'already in database, stock: {row[1]}')

    @classmethod
    def create_default_portfolios(cls,):
        default = User.objects.get(username='default_user')

        # portfolio = Portfolio.objects.create(portfolio_name='Techno', user=default)
        # for stock_symbol in stock_lists.get('TECH'):
        #     stock = Stock.objects.get(symbol=stock_symbol)
        #     stock_selection = StockSelection.objects.create(stock=stock,
        #         quantity=1, portfolio=portfolio)

        portfolio = Portfolio.objects.create(
            portfolio_name='AEX', user=default)
        for stock_symbol in stock_lists.get('AEX'):
            stock = Stock.objects.get(symbol=stock_symbol)
            _ = StockSelection.objects.create(
                stock=stock, quantity=1, portfolio=portfolio)

        # portfolio = Portfolio.objects.create(portfolio_name='Dow Jones', user=default)
        # for stock_symbol in stock_lists.get('DOW'):
        #     print(stock_symbol)
        #     stock = Stock.objects.get(symbol=stock_symbol)
        #     stock_selection = StockSelection.objects.create(stock=stock,
        #         quantity=1, portfolio=portfolio)


class WorldTradingData:
    ''' methods to handle trading data
        website: https://www.worldtradingdata.com
    '''
    up_triangle = '\u25B2'    # black up triangle
    down_triangle = '\u25BC'  # black down triangle
    rectangle = '\u25AC'      # black rectangle

    @classmethod
    def setup(cls,):
        cls.api_token = config('API_token')
        cls.stock_url = 'https://api.worldtradingdata.com/api/v1/stock'
        cls.intraday_url = 'https://intraday.worldtradingdata.com/api/v1/intraday'
        cls.history_url = 'https://api.worldtradingdata.com/api/v1/history'
        cls.forex_url = 'https://api.worldtradingdata.com/api/v1/forex'

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
    def get_stock_trade_info(cls, stock_symbols):
        ''' return the stock trade info as a dict retrieved from url json, key 'data'
        '''
        params = {'symbol': ','.join(stock_symbols).upper(),
                  'sort': 'name',
                  'api_token': cls.api_token}

        orig_stock_info = {}
        if stock_symbols:
            try:
                res = requests.get(cls.stock_url, params=params)
                if res:
                    orig_stock_info = res.json().get('data', {})
                else:
                    pass

            except requests.exceptions.ConnectionError:
                logger.info(f'connection error: {cls.stock_url} {params}')

        else:
            pass

        if len(stock_symbols) > MAX_SYMBOLS_ALLOWED:
            logger.info(f'warning - number of symbols exceed '
                        f'maximum of {MAX_SYMBOLS_ALLOWED}')

        # if there is stock info, convert date string to datetime object
        # and add display attributes
        stock_info = []
        if orig_stock_info:
            for stock in orig_stock_info:
                stock['last_trade_time'] = datetime.datetime.strptime(
                    stock.get('last_trade_time'), "%Y-%m-%d %H:%M:%S")

                try:
                    _ = float(stock.get('change_pct'))

                except ValueError:
                    stock['change_pct'] = '0'

                if abs(float(stock.get('change_pct'))) < 0.001:
                    stock['font_color'] = 'black'
                    stock['caret_up_down'] = cls.rectangle

                elif float(stock.get('change_pct')) < 0:
                    stock['font_color'] = 'red'
                    stock['caret_up_down'] = cls.down_triangle

                else:
                    stock['font_color'] = 'green'
                    stock['caret_up_down'] = cls.up_triangle

                stock_info.append(stock)

            stock_info = sorted(stock_info, key=lambda i: i['name'])

        return stock_info

    @classmethod
    def get_stock_intraday_info(cls, stock_symbol):
        '''  return stock intraday info as a dict retrieved from url json,
             key 'intraday'
        '''
        # range: number of days (1-30), interval: in minutes
        params = {'symbol': stock_symbol.upper(),
                  'range': '1',
                  'interval': '5',
                  'sort': 'asc',
                  'api_token': cls.api_token}

        intraday_info = {}
        try:
            res = requests.get(cls.intraday_url, params=params)
            if res:
                intraday_info = res.json().get('intraday', {})
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {cls.intraday_url} {params}')

        # if there is intraday info, convert date string and provide time and
        # create list of trade_info tuples
        trade = namedtuple('trade', 'date open close low high volume')
        intraday_trades = []
        min_low = None
        max_high = None
        if intraday_info:
            for time_stamp, trade_info in intraday_info.items():
                intraday_trades.append(
                    trade(date=datetime.datetime.strptime(
                        time_stamp, "%Y-%m-%d %H:%M:%S"),
                          open=trade_info.get('open'),
                          close=trade_info.get('close'),
                          low=trade_info.get('low'),
                          high=trade_info.get('high'),
                          volume=trade_info.get('volume'),
                         )
                    )

                min_low = get_min(trade_info.get('low'), min_low)
                max_high = get_max(trade_info.get('high'), max_high)

            initial_open = intraday_trades[0].open
            last_close = intraday_trades[-1].close

            # add start and end time
            start_time = intraday_trades[0].date.strftime("%Y-%m-%d") + ' 08:00:00'
            intraday_trades.insert(
                0, trade(date=datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
                         open=None, close=None, low=None, high=None, volume=None
                        ))
            end_time = intraday_trades[-1].date.strftime("%Y-%m-%d") + ' 18:00:00'
            intraday_trades.append(
                trade(date=datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
                      open=initial_open, close=last_close, low=min_low,
                      high=max_high, volume=None,
                     ))
        else:
            logger.info(f'unable to get stock intraday data for '
                        f'{cls.intraday_url} {params}')

        return intraday_trades

    @classmethod
    def get_stock_history_info(cls, stock_symbol):
        '''  return stock history info as a dict retrieved from url json,
             key 'history'
        '''
        params = {'symbol': stock_symbol.upper(),
                  'sort': 'newest',
                  'api_token': cls.api_token}

        history_info = {}
        try:
            res = requests.get(cls.history_url, params=params)
            if res:
                history_info = res.json().get('history', {})
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {cls.history_url} {params}')

        # if there is intraday info, convert date string and provide date and
        # create list of trade_info tuples
        trade = namedtuple('trade', 'date open close low high volume')
        history_trades = []
        if history_info:
            for date_stamp, trade_info in history_info.items():
                history_trades.append(
                    trade(date=datetime.datetime.strptime(date_stamp, "%Y-%m-%d"),
                          open=trade_info.get('open'),
                          close=trade_info.get('close'),
                          low=trade_info.get('low'),
                          high=trade_info.get('high'),
                          volume=trade_info.get('volume'),
                         )
                    )

        else:
            logger.info(f'unable to get stock history data for '
                        f'{cls.history_url} {params}')

        return history_trades

    @classmethod
    def parse_stock_name(cls, stock_string, markets=None):
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
    def get_portfolio_stock_info(cls, portfolio):
        symbols_quantities = {stock.stock.symbol: stock.quantity \
            for stock in portfolio.stocks.all()}
        list_symbols = list(symbols_quantities.keys())
        stock_trade_info = cls.get_stock_trade_info(
            list_symbols[0:MAX_SYMBOLS_ALLOWED])
        stock_trade_info += cls.get_stock_trade_info(
            list_symbols[MAX_SYMBOLS_ALLOWED:2*MAX_SYMBOLS_ALLOWED])

        stock_info = []
        for stock in stock_trade_info:
            stock['quantity'] = symbols_quantities[stock['symbol']]

            try:
                stock['amount'] = f'{d(stock["quantity"]) * d(stock["price"]):,.2f}'

            except NameError:
                stock['amount'] = 'n/a'

            stock_info.append(stock)

        if stock_info:
            stock_info = sorted(stock_info, key=lambda i: i['name'])

        return stock_info

    @classmethod
    def calculate_stocks_value(cls, stocks, currency):
        total_value = d('0')
        if not stocks:
            return total_value

        for stock in stocks:
            base_value = d(stock['quantity']) * d(stock['price'])
            exchange_rate = Currency.objects.get(
                currency=stock['currency']).usd_exchange_rate
            usd_value = d(base_value) / d(exchange_rate)
            total_value += usd_value

        if currency == 'USD':
            pass

        elif currency == 'EUR':
            exchange_rate_euro = Currency.objects.get(
                currency='EUR').usd_exchange_rate
            total_value *= d(exchange_rate_euro)

        else:
            assert False, f'incorrect currency used: {currency}'

        return total_value

    @classmethod
    def update_currencies(cls):
        params = {'base': 'USD',
                  'api_token': cls.api_token}

        forex_dict = {}
        try:
            res = requests.get(cls.forex_url, params=params)
            if res:
                forex_dict = res.json().get('data', {})
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {cls.forex_url} {params}')

        if forex_dict:
            for cur in Currency.objects.all().order_by('currency'):
                currency_key = cur.currency
                currency_object = Currency.objects.get(currency=currency_key)
                usd_exchange_rate = forex_dict.get(currency_key, '')

                if usd_exchange_rate:
                    currency_object.usd_exchange_rate = usd_exchange_rate
                    currency_object.save()
        else:
            logger.info(f'unable to get currency data for {cls.forex_url} {params}')


def update_currencies_at_interval(interval=UPDATE_INTERVAL):
    '''  update the currencies depending on interval in seconds
         default value is 6 hours (21600 seconds)
    '''
    assert isinstance(interval, int), \
           f'check interval setting {interval} must be an integer'

    wtd = WorldTradingData()
    wtd.setup()
    start_time = time.time()
    current_time = start_time
    elapsed_time = int(current_time - start_time)

    while True:
        if elapsed_time % interval == 0:
            wtd.update_currencies()

            time_str = datetime.datetime.fromtimestamp(
                current_time).strftime('%d-%m-%Y %H:%M:%S')
            logger.info(f'update currencies at {time_str}')

            # sleep one second to make sure update is only done once in a second
            time.sleep(1)

        current_time = time.time()
        elapsed_time = int(current_time - start_time)

def start_currency_update():
    thread_update_currencies = threading.Thread(
        target=update_currencies_at_interval, kwargs={'interval': UPDATE_INTERVAL})
    thread_update_currencies.start()
    logger.info(f'currency update thread '
                f'{start_currency_update.__name__} has started ...')
