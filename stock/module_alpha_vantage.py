import requests
import datetime
from decouple import config
from howdimain.utils.plogger import Logger


logger = Logger.getlogger()
api_token = config('API_token_Alpha_Vantage')
stock_url = 'https://www.alphavantage.co/query'

def get_stock_alpha_vantage(stock_symbols):
    ''' return the stock trade info as a dict
    '''
    stock_info = []
    for symbol in stock_symbols:

        params = {'symbol': symbol.upper(),
                  'function' : 'GLOBAL_QUOTE',
                  'apikey': api_token
        }

        try:
            res_dict = requests.get(stock_url, params=params).json()

        except requests.exceptions.ConnectionError:
            logger.info(f'connection error: {stock_url} {params}')

        stock_dict = {}
        if res_dict:
            stock_dict['symbol'] = (
                res_dict.get('Global Quote').get('01. symbol'))
            stock_dict['open'] = (
                res_dict.get('Global Quote').get('02. open'))
            stock_dict['high'] = (
                res_dict.get('Global Quote').get('03. high'))
            stock_dict['low'] = (
                res_dict.get('Global Quote').get('04. low'))
            stock_dict['price'] = (
                res_dict.get('Global Quote').get('05. price'))
            stock_dict['volume'] = (
                res_dict.get('Global Quote').get('06. volume'))
            stock_dict['last_trade_time'] = (
                res_dict.get('Global Quote').get('07. latest trading day'))
            stock_dict['close yesterday'] = (
                res_dict.get('Global Quote').get('08. previous close'))
            stock_dict['day_change'] = (
                res_dict.get('Global Quote').get('09. change'))
            stock_dict['change_pct'] = (
                res_dict.get('Global Quote').get('10. change percent'))

            )

            # convert date string to datetime object
            # if there is no last_trade_time then skip this stock
            for stock in orig_stock_info:
            try:
                stock['last_trade_time'] = datetime.datetime.strptime(
                    stock.get('last_trade_time'), "%Y-%m-%d %H:%M:%S")
                stock_info.append(stock)

            except ValueError:
                continue

            stock_info.append(stock_dict)

    return stock_info
