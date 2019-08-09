import datetime
from collections import namedtuple
import requests
import csv
import json
from .models import Exchange, Currency, Stock
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.min_max import get_min, get_max
from decouple import config

from .test_data import test_json

logger = Logger.getlogger()

class PopulateStock:

    def read_csv(cls, filename):
        cls.stock_data = []
        with open(filename) as csv_file:
            _stock_data = csv.reader(csv_file, delimiter=",")
            # skip the header
            next(_stock_data, None)
            for row in _stock_data:
                cls.stock_data.append(row)

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


class WorldTradingData:
    ''' methods to handle trading data
        website: https://www.worldtradingdata.com
    '''
    up_triangle = '\u25B3'    # white up triangle
    down_triangle = '\u25BD'  # white down triangle
    rectangle = '\u25AD'      # white rectangle

    def setup(cls,):
        cls.api_token = config('API_token')
        cls.stock_url = 'https://api.worldtradingdata.com/api/v1/stock'
        cls.intraday_url = 'https://intraday.worldtradingdata.com/api/v1/intraday'
        cls.range = '1'     #  number of days (1-30)
        cls.interval = '5'  #  interval in minutes

        cls.schema = [{'name': 'Time',
                       'type': 'date',
                       'format': '%d-%m-%Y %-I:%-M',
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
                      },
                     ]

    def get_stock_trade_info(cls, stock_symbols):
        ''' return the stock trade info as a dict retrieved from url json, key 'data'
        '''
        url = ''.join([cls.stock_url,
                       '?symbol=' + ','.join(stock_symbols).upper(),
                       '&sort_by=name',
                       '&api_token=' + cls.api_token],
                       )

        res = requests.get(url)
        try:
            res.raise_for_status()
        except Exception as exception:
            logger.info(f'unable to get stock data for {url}')
            return []

        orig_stock_info = json.loads(res.content).get('data')

        # if there is stock info, convert date string to datetime object
        # and add display attributes
        stock_info = []
        if orig_stock_info:
            for stock in orig_stock_info:
                stock['last_trade_time'] = datetime.datetime.strptime(
                    stock.get('last_trade_time'), "%Y-%m-%d %H:%M:%S")

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

    def get_stock_intraday_info(cls, stock_symbol):
        '''  return stock intraday info as a dict retrieved from url json, key 'data'
        '''
        url = ''.join([cls.intraday_url,
                       '?symbol=' + stock_symbol.upper(),
                       '&range=' + cls.range,
                       '&interval=' + cls.interval,
                       '&sort=asc'
                       '&api_token=' + cls.api_token],
                       )

        res = requests.get(url)
        try:
            res.raise_for_status()
        except Exception as exception:
            logger.info(f'unable to get stock data for {url}')
            return []
        intraday_info = json.loads(res.content).get('intraday')

        # if there is intraday info, convert date string and provide time and
        # create list of date/time, price tuples
        trade = namedtuple('trade', 'time open close low high volume')
        intraday_trades = []
        min_low = None; max_high = None
        if intraday_info:
            for time_stamp, price_info in intraday_info.items():
                intraday_trades.append(
                    trade(time=datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S"),
                          open=price_info.get('open'),
                          close=price_info.get('close'),
                          low=price_info.get('low'),
                          high=price_info.get('high'),
                          volume=price_info.get('volume'),
                          )
                    )

                min_low = get_min(price_info.get('low'), min_low)
                max_high = get_max(price_info.get('high'), max_high)

            initial_open = intraday_trades[0].open
            last_close = intraday_trades[-1].close

            # add start and end time
            start_time = intraday_trades[0].time.strftime("%Y-%m-%d") + ' 08:00:00'
            intraday_trades.insert(0,
                    trade(time=datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
                          open=None, close=None, low=None, high=None, volume=None)
                    )
            end_time = intraday_trades[-1].time.strftime("%Y-%m-%d") + ' 18:00:00'
            intraday_trades.append(
                    trade(time=datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
                          open=initial_open, close=last_close, low=min_low, high=max_high, volume=None)
                    )

        return intraday_trades


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