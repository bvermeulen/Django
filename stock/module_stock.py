import threading
import datetime
import time
from collections import namedtuple
import requests
from requests.exceptions import ConnectionError
import csv
import json
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import Exchange, Currency, Stock, Portfolio, StockSelection
from .stock_lists import stock_lists
from howdimain.utils.plogger import Logger
from howdimain.utils.min_max import get_min, get_max
from decouple import config
from decimal import Decimal as d

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
                stock = Stock.objects.create(
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

        portfolio = Portfolio.objects.create(portfolio_name='AEX',
            user=default)
        for stock_symbol in stock_lists.get('AEX'):
            stock = Stock.objects.get(symbol=stock_symbol)
            stock_selection = StockSelection.objects.create(stock=stock,
                quantity=1, portfolio=portfolio)

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
        cls.max_symbols_allowed = 20

    @staticmethod
    def get_schema(format):
        return [{'name': 'Date',
                 'type': 'date',
                 'format': format,
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
        url = ''.join([cls.stock_url,
                       '?symbol=' + ','.join(stock_symbols).upper(),
                       '&sort_by=name',
                       '&api_token=' + cls.api_token],
                       )
        if stock_symbols:
            try:
                res = requests.get(url)
                orig_stock_info = json.loads(res.content).get('data', {})

            except ConnectionError:
                orig_stock_info = {}
                print(f'connection error: {url}')
                logger.info(f'connection error: {url}')

        else:
            orig_stock_info = {}

        if len(stock_symbols) > cls.max_symbols_allowed:
            logger.info(f'warning - number of symbols exceed maximum of {cls.max_symbols_allowed}')

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

        return stock_info

    @classmethod
    def get_stock_intraday_info(cls, stock_symbol):
        '''  return stock intraday info as a dict retrieved from url json, key 'data'
        '''
        range = '1'     #  number of days (1-30)
        interval = '5'  #  interval in minutes
        url = ''.join([cls.intraday_url,
                       '?symbol=' + stock_symbol.upper(),
                       '&range=' + range,
                       '&interval=' + interval,
                       '&sort=asc'
                       '&api_token=' + cls.api_token ],
                       )

        try:
           res = requests.get(url)
           intraday_info = json.loads(res.content).get('intraday', {})

        except ConnectionError:
            intraday_info = {}
            print(f'connection error: {url}')
            logger.info(f'connection error: {url}')

        # if there is intraday info, convert date string and provide time and
        # create list of trade_info tuples
        trade = namedtuple('trade', 'date open close low high volume')
        intraday_trades = []
        min_low = None; max_high = None
        if intraday_info:
            for time_stamp, trade_info in intraday_info.items():
                intraday_trades.append(
                    trade(date=datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S"),
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
            intraday_trades.insert(0,
                    trade(date=datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
                          open=None, close=None, low=None, high=None, volume=None)
                    )
            end_time = intraday_trades[-1].date.strftime("%Y-%m-%d") + ' 18:00:00'
            intraday_trades.append(
                    trade(date=datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
                          open=initial_open, close=last_close, low=min_low, high=max_high, volume=None)
                    )
        else:
            logger.info(f'unable to get stock intraday data for {url}')

        return intraday_trades

    @classmethod
    def get_stock_history_info(cls, stock_symbol):
        '''  return stock history info as a dict retrieved from url json, key 'data'
        '''
        url = ''.join([cls.history_url,
                       '?symbol=' + stock_symbol.upper(),
                       '&sort=newest',
                       '&api_token=' + cls.api_token],
                       )

        try:
            res = requests.get(url)
            history_info = json.loads(res.content).get('history', {})

        except ConnectionError:
            history_info = {}
            print(f'connection error: {url}')
            logger.info(f'connection error: {url}')

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
            logger.info(f'unable to get stock history data for {url}')

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
            list_symbols[0:cls.max_symbols_allowed])
        stock_trade_info += cls.get_stock_trade_info(
            list_symbols[cls.max_symbols_allowed:2*cls.max_symbols_allowed])

        stock_info = []
        for stock in stock_trade_info:
            stock['quantity'] = symbols_quantities[stock['symbol']]

            try:
                stock['amount'] = f'{d(stock["quantity"]) * d(stock["price"]):,.2f}'

            except NameError:
                stock['amount'] = 'n/a'

            stock_info.append(stock)

        return sorted(stock_info, key = lambda i: i['name'])

    @classmethod
    def update_currencies(cls):
        base_currency = 'USD'
        url = ''.join([cls.forex_url,
                       '?base=' + base_currency,
                       '&api_token=' + cls.api_token ],
        )
        try:
            res = requests.get(url)
            forex_dict = json.loads(res.content).get('data', {})

        except ConnectionError:
            forex_dict = {}
            print(f'connection error: {url}')
            logger.info(f'connection error: {url}')

        for cur in Currency.objects.all().order_by('currency'):
            currency_key = cur.currency
            currency_object = Currency.objects.get(currency=currency_key)
            usd_exchange_rate = forex_dict.get(currency_key, '')

            if usd_exchange_rate:
                currency_object.usd_exchange_rate = usd_exchange_rate
                currency_object.save()


def update_currencies_at_interval(interval=21600):
    '''  update the currency depending on interval in seconds
         default value is 6 hours (21600 seconds
    '''
    assert isinstance(interval, int), f'check interval setting {interval} must be an integer'

    wtd = WorldTradingData()
    wtd.setup()
    start_time = time.time()
    current_time = start_time
    elapsed_time = int(current_time - start_time)

    while True:
        if elapsed_time % interval == 0:
            wtd.update_currencies()
            time_str = datetime.datetime.fromtimestamp(current_time).strftime('%d-%m-%Y %H:%M:%S')
            print(f'update currencies at {time_str}')
            logger.info(f'update currencies at {time_str}')

        current_time = time.time()
        elapsed_time = int(current_time - start_time)


thread_update_currencies = threading.Thread(
    target=update_currencies_at_interval, kwargs={'interval':21600})
thread_update_currencies.start()
