import datetime
import pytz
import requests
from decouple import config
from howdimain.utils.plogger import Logger
from stock.models import Stock



logger = Logger.getlogger()
api_token = config('API_token_Alpha_Vantage')
stock_url = 'https://www.alphavantage.co/query'

def get_stock_alpha_vantage(stock_symbols):
    ''' return the stock trade info as a dict
    '''
    print(stock_symbols)
    stock_info = []
    for symbol in stock_symbols:

        symbol = symbol.upper()
        params = {
            'symbol': symbol,
            'function' : 'GLOBAL_QUOTE',
            'apikey': api_token
        }

        try:
            res = requests.get(stock_url, params=params)
            quote_dict = res.json().get('Global Quote', {})

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {stock_url} {params}')
            quote_dict = {}

        # get other stock info from the database if does not exist skip this quote
        try:
            stock_db = Stock.objects.get(symbol=symbol)

        except Stock.DoesNotExist:
            quote_dict = {}

        stock_dict = {}
        if quote_dict:
            stock_dict['symbol'] = quote_dict.get('01. symbol')
            stock_dict['open'] = quote_dict.get('02. open')
            stock_dict['day_high'] = quote_dict.get('03. high')
            stock_dict['day_low'] = quote_dict.get('04. low')
            stock_dict['price'] = quote_dict.get('05. price')
            stock_dict['volume'] = quote_dict.get('06. volume')
            _date_trade = quote_dict.get('07. latest trading day')
            stock_dict['close_yesterday'] = quote_dict.get('08. previous close')
            stock_dict['day_change'] = quote_dict.get('09. change')
            stock_dict['change_pct'] = quote_dict.get('10. change percent')[:-1]

            stock_dict['name'] = stock_db.company
            stock_dict['currency'] = stock_db.currency.currency
            stock_dict['stock_exchange_short'] = stock_db.exchange.exchange_short

            # convert date_time string to datetime object if not possible skip the quote
            try:
                _time_stock = datetime.datetime.now(
                    pytz.timezone(stock_db.exchange.time_zone_name))
                _date_trade = datetime.datetime.strptime(_date_trade), '%Y-%m-%d')

                if _time_stock.date <> _date_trade.date:
                    _time_stock = datetime,datetime.strftime('18:00:00', '%H:%M:%S')

                _date_time = datetime.datetime.strptime(_date_time, '%Y-%m-%d %H:%M:%S')
                stock_dict['last_trade_time'] = _date_time

            except ValueError:
                continue

            stock_info.append(stock_dict)
            print(stock_dict)

    return stock_info
