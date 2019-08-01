from .models import Exchange, Currency, Stock
from django.db.utils import IntegrityError
import requests
import csv
import json
from pprint import pprint
from howdimain.utils.plogger import Logger
from decouple import config

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
    def setup(cls,):
        cls.api_token = config('API_token')
        cls.stock_url = 'https://api.worldtradingdata.com/api/v1/stock'
        cls.intraday_url = 'https://intraday.worldtradingdata.com/api/v1/intraday'

    def get_data(cls, *stock_symbols):
        symbols = ','.join(cls.stock_symbols).upper()
        symbols = '?symbol=' + symbols
        token = '&api_token=' + cls.api_token
        url = ''.join([cls.stock_url,
                       symbols,
                       token])
        res = requests.get(url)
        try:
            res.raise_for_status()
        except Exception as exception:
            print(f'exception: {exception}')

        stock_dict = json.loads(res.content)
        pprint(stock_dict)

    def parse_stock_name(cls, *stock_names, markets=None):
        ''' parse stock names searching the worldtradingdata database in three
            passes: 1) is the stock name the actual ticker symbol,
            2) if not does it start with the stock_name or 3) does the company
            name contain the stock_name.

            arguments: stock names, like: 'Wolters', 'AAPL', 'msft'
            returns: list of ticker symbols

            Stock is Django model containing stock information
        '''
        if markets is None:
            markets = []

        #  use set to avoid duplicates
        cls.stock_symbols = set()

        def add_stock_symbol_if_valid(stock_symbol):
            '''  only add if stock_symbol is listed on one of the markets or
                 markets is empty
            '''
            if markets == [] or Stock.objects.filter(symbol=stock_symbol).\
                                    first().exchange.exchange_short in markets:
                cls.stock_symbols.add(stock_symbol)
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
                for stock in Stock.objects.filter(company__contains=stock_name):
                    stock_symbol = Stock.objects.get(symbol=stock.symbol).symbol
                    add_stock_symbol_if_valid(stock_symbol)


        cls.stock_symbols = list(cls.stock_symbols)
