import datetime
from collections import namedtuple
import pytz
import requests
from decouple import config
from howdimain.utils.min_max import get_min, get_max
from howdimain.utils.plogger import Logger
from stock.models import Stock


logger = Logger.getlogger()
api_token = config('API_token_Alpha_Vantage')
stock_url = 'https://www.alphavantage.co/query'
intraday_url = 'https://www.alphavantage.co/query'

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

            # check date of last trade. If not today's date then make 18:00
            # otherwise take today's date and time
            try:
                timezone_stock = stock_db.exchange.time_zone_name.upper()
                # Handle Japanese time zone
                if timezone_stock == 'JST':
                    timezone_stock = 'Asia/Tokyo'

                _date_time = datetime.datetime.now(
                    pytz.timezone(timezone_stock)).replace(tzinfo=None)
                _date_trade = datetime.datetime.strptime(_date_trade, '%Y-%m-%d')

                if  datetime.time(9, 0, 0) < _date_time.time() < datetime.time(18, 0, 0):
                    pass

                else:
                    _date_time = datetime.datetime.combine(
                        _date_trade.date(), datetime.datetime.strptime(
                            '18:00:00', '%H:%M:%S').time())

                stock_dict['last_trade_time'] = _date_time

            except ValueError:
                continue

            stock_info.append(stock_dict)
            print(stock_dict)

    return stock_info


def get_intraday_alpha_vantage(symbol):

    symbol = symbol.upper()
    params = {'symbol': symbol,
              'function': 'TIME_SERIES_INTRADAY',
              'interval': '5min',
              'apikey': api_token}

    meta_data = {}
    time_series = {}
    try:
        res = requests.get(intraday_url, params=params)
        if res:
            meta_data = res.json().get('Meta Data', {})
            time_series = res.json().get('Time Series (5min)', {})

    except requests.exceptions.ConnectionError:
        logger.info(f'connection error: {intraday_url} {params}')

    if not meta_data or not time_series:
        return []

    try:
        stock_db = Stock.objects.get(symbol=symbol)

    except Stock.DoesNotExist:
        return []

    timezone_stock = stock_db.exchange.time_zone_name.upper()
    timezone_EST = 'EST'
    # Handle Japanese time zone
    if timezone_stock == 'JST':
        timezone_stock = 'Asia/Tokyo'

    trade_tuple = namedtuple('trade', 'date open close low high volume')
    intraday_trades = []
    min_low = None
    max_high = None
    last_trade = datetime.datetime.strptime(
        meta_data.get('3. Last Refreshed'), '%Y-%m-%d %H:%M:%S').replace(
            tzinfo=pytz.timezone(timezone_EST)).astimezone(pytz.timezone(timezone_stock))

    for time_stamp, trade_info in time_series.items():
        time_stamp = datetime.datetime.strptime(
            time_stamp, '%Y-%m-%d %H:%M:%S').replace(
                tzinfo=pytz.timezone(timezone_EST)).astimezone(
                    pytz.timezone(timezone_stock))

        if time_stamp.date() == last_trade.date():
            trade = trade_tuple(
                date=time_stamp.replace(tzinfo=None),
                open=trade_info.get('1. open'),
                high=trade_info.get('2. high'),
                low=trade_info.get('3. low'),
                close=trade_info.get('4. close'),
                volume=trade_info.get('5. volume'),
            )
            intraday_trades.append(trade)

            min_low = get_min(trade.low, min_low)
            max_high = get_max(trade.high, max_high)

    # reverse sorting on timestamp
    intraday_trades = sorted(intraday_trades, key=lambda k: k.date)

    # add start and end time
    initial_open = intraday_trades[0].open
    last_close = intraday_trades[-1].close
    start_time = intraday_trades[0].date.strftime("%Y-%m-%d") + ' 08:00:00'
    intraday_trades.insert(
        0, trade_tuple(date=datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
                       open=None, close=None, low=None, high=None, volume=None
                      ))
    end_time = intraday_trades[-1].date.strftime("%Y-%m-%d") + ' 18:00:00'
    intraday_trades.append(
        trade_tuple(date=datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
                    open=initial_open, close=last_close, low=min_low,
                    high=max_high, volume=None,
                   ))

    return intraday_trades
