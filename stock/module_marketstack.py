import datetime
from collections import namedtuple
import requests
from decouple import config
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED
from howdimain.utils.last_tradetime import last_trade_time
from howdimain.utils.plogger import Logger
from stock.models import Stock


logger = Logger.getlogger()
api_token = config('access_key_marketstack')
marketstack_api_url = 'https://api.marketstack.com/v1/'


def convert_stock_symbols(symbols_ric: list) -> list:

    symbols_mic = []
    for symbol_ric in symbols_ric:
        try:
            symbols_mic.append(Stock.objects.get(symbol_ric=symbol_ric).symbol)

        except Stock.DoesNotExist:
            pass

    return symbols_mic


def get_stock_marketstack(stock_symbols: list) -> dict:
    ''' return the stock trade info as a dict
    '''
    stock_symbols = convert_stock_symbols(stock_symbols)

    symbols = ','.join(stock_symbols).upper()
    stock_url = marketstack_api_url + 'eod/latest'
    params = {
        'symbols': symbols,
        'access_key': api_token,
    }

    stock_list = []
    if stock_symbols:
        try:
            res = requests.get(stock_url, params=params)
            if res and res.status_code == 200:
                stock_list = res.json().get('data')
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {stock_url} {params}')

    else:
        pass

    if len(stock_symbols) > MAX_SYMBOLS_ALLOWED:
        logger.warning(f'number of symbols exceed maximum of {MAX_SYMBOLS_ALLOWED}')

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
        stock_dict['exchange_mic'] = stock_db.exchange.mic
        stock_dict['symbol'] = stock_db.symbol_ric
        stock_dict['name'] = stock_db.company
        stock_dict['open'] = quote.get('open')
        stock_dict['day_high'] = quote.get('high')
        stock_dict['day_low'] = quote.get('low')
        stock_dict['price'] = quote.get('close')
        stock_dict['volume'] = quote.get('volume')
        stock_dict['close_yesterday'] = quote.get('open')
        stock_dict['day_change'] = quote.get('change', '0')
        stock_dict['change_pct'] = quote.get('changepercentage', '0')
        stock_dict['last_trade_time'] = last_trade_time(
            quote.get('date'), stock_dict['exchange_mic']
        )
        stock_info.append(stock_dict)

    return stock_info


def get_intraday_marketstack(symbol: str) -> list:
    ''' marketstack intraday quotes are on the Investors Exchange (IEXG) and
        not implemented as yet, they should be covered by Financial Modeling Prep
    '''
    return []


def get_history_marketstack(symbol):
    symbol = symbol.upper()
    symbol = convert_stock_symbols([symbol])

    history_url = marketstack_api_url + 'eod'
    offset = 0
    params = {'symbols': symbol,
              'offset': offset,
              'access_key': api_token}

    history_series = {}
    try:
        res = requests.get(history_url, params=params)
        limit = res.json().get('pagination').get('limit')
        if res:
            pages = res.json().get('pagination').get('total') // limit

            history_series = res.json().get('data', {})

    except requests.exceptions.ConnectionError:
        logger.info(f'connection error: {history_url} {params}')

    if not history_series:
        return []

    # if there is history info, convert date string and provide date and
    # create list of trade_info tuples
    trade = namedtuple('trade', 'date open close low high volume')
    history_trades = []

    for _ in range(0, pages + 1):

        _history_trades = []
        for trade_info in history_series:
            _history_trades.append(trade(
                date=datetime.datetime.strptime(trade_info.get('date')[0:10], "%Y-%m-%d"),
                open=trade_info.get('open'),
                close=trade_info.get('high'),
                low=trade_info.get('low'),
                high=trade_info.get('close'),
                volume=trade_info.get('volume'),
            ))

        history_trades += _history_trades
        offset += limit
        params = {
            'symbols': symbol,
            'offset': offset,
            'access_key': api_token}

        try:
            res = requests.get(history_url, params=params)

            if res:
                history_series = res.json().get('data', {})

            else:
                break

        except requests.exceptions.ConnectionError:
            break

    if not history_trades:
        logger.info(f'unable to get stock history data for '
                    f'{history_url} {params}')

    return history_trades
