''' extract Marketstack exchanges and stocks
'''
import pandas as pd
import requests
from decouple import config

MIC_RIC_table = {
    'XNAS': 'None',
    'XNYS': 'None',
    'ARCX': 'None',
    'OTCM': 'None',
    'XBUE': 'BA',
    'XBAH': 'BH',
    'XBRU': 'BR',
    'BVMF': 'SA',
    'XTSE': 'TO',
    'XTSX': 'V',
    'XCNQ': 'CN',
    'XSGO': 'SN',
    'XSHG': 'SS',
    'XSHE': 'SZ',
    'XBOG': 'XBOG',
    'XCSE': 'CO',
    'XCAI': 'XCAI',
    'XTAL': 'TL',
    'XHEL': 'HE',
    'XPAR': 'PA',
    'XFRA': 'F',
    'XSTU': 'SG',
    'XETRA': 'DE',
    'XHKG': 'HK',
    'XICE': 'IC',
    'XBOM': 'BO',
    'XNSE': 'NS',
    'XIDX': 'JK',
    'XTAE': 'TA',
    'XMIL': 'MI',
    'XTKS': 'T',
    'XNGO': 'NG',
    'XFKA': 'FU',
    'XSAP': 'SP',
    'XRIS': 'RI',
    'XLIT': 'VL',
    'XKLS': 'KL',
    'XMEX': 'MX',
    'XAMS': 'AS',
    'XNZE': 'NZ',
    'XNSA': 'LG',
    'XOSL': 'OL',
    'XLIM': 'LM',
    'XWAR': 'WA',
    'XLIS': 'LS',
    'DSMD': 'QA',
    'MISX': 'ME',
    'XSAU': 'SR',
    'XBEL': 'XBEL',
    'XSES': 'SI',
    'XJSE': 'JO',
    'XKRX': 'KS',
    'BMEX': 'MC',
    'XSTO': 'ST',
    'XSWX': 'SW',
    'XTAI': 'TW',
    'XBKK': 'BK',
    'XIST': 'IS',
    'XDFM': 'DU',
    'XLON': 'L',
    'XSTC': 'XSTC',
    'XASE': 'None',
    'XASX': 'AX',
    'XCBO': 'None',
    'NMFQS': 'None',
    'OOTC': 'None',
    'PSGM': 'None',
    'OTCB': 'None',
    'OTCQ': 'None',
    'PINC': 'None',
    'IEXG': 'None',
}

base_url = 'https://api.marketstack.com/v1/'
api_key = config('access_key_marketstack')
exchanges_filename = 'marketstack_exchanges.xlsx'
stocks_filename = 'marketstack_stocks.xlsx'

# extract exchanges
url = base_url + 'exchanges'
offset = 0
params = {
    'limit': 1000,
    'offset': offset,
    'access_key': api_key,
}

res = requests.get(url, params)

exchanges = {
    'mic': [],
    'ric': [],
    'name': [],
    'acronym': [],
    'country': [],
    'country_code': [],
    'city': [],
    'website': [],
    'timezone': [],
    'currency': []
}

for exchange in res.json().get('data'):
    exchanges['mic'].append(exchange.get('mic'))
    exchanges['ric'].append(MIC_RIC_table.get(exchange.get('mic')))
    exchanges['name'].append(exchange.get('name'))
    exchanges['acronym'].append(exchange.get('acronym'))
    exchanges['country'].append(exchange.get('country'))
    exchanges['country_code'].append(exchange.get('country_code'))
    exchanges['city'].append(exchange.get('city'))
    exchanges['website'].append(exchange.get('website'))
    exchanges['timezone'].append(exchange.get('timezone').get('timezone'))
    exchanges['currency'].append(exchange.get('currency').get('code'))

exchanges_df = pd.DataFrame(exchanges)
exchanges_df.to_excel(exchanges_filename)

# extract stocks
stocks = {
    'symbol': [],
    'symbol_ric': [],
    'name': [],
    'has_intraday': [],
    'has_eod': [],
    'exchange_name': [],
    'exchange_acronym': [],
    'exchange_mic': [],
    'exchange_currency': [],
    'exchange_country': [],
    'exchange_city': [],
    'exchange_website': [],
}

url = base_url + 'tickers'
offset = 0
params = {
    'limit': 1000,
    'offset': offset,
    'access_key': api_key,
}
res = requests.get(url, params)
total_stocks = res.json().get('pagination').get('total')
pages = total_stocks // 1000
print(f'Total {total_stocks} stocks and {pages} pages')

for page in range(0, pages + 1):
    print(f'\rProcessing page {page:4} from {offset:6} to {offset+999:6} ...', end='')

    stocks_data = res.json().get('data')
    for stock in stocks_data:
        symbol_mic = stock.get('symbol')
        symbol_parsed = symbol_mic.split('.')
        if len(symbol_parsed) == 2:
            symbol_ric = symbol_parsed[0] + '.' + MIC_RIC_table.get(symbol_parsed[1], 'CHECKED')
        else:
            symbol_ric = symbol_mic

        stocks['symbol'].append(symbol_mic)
        stocks['symbol_ric'].append(symbol_ric)
        stocks['name'].append(stock.get('name'))
        stocks['has_intraday'].append(stock.get('has_intraday'))
        stocks['has_eod'].append(stock.get('has_eod'))
        stocks['exchange_name'].append(stock.get('stock_exchange').get('name'))
        stocks['exchange_acronym'].append(stock.get('stock_exchange').get('acronym'))
        stocks['exchange_mic'].append(stock.get('stock_exchange').get('mic'))
        stocks['exchange_currency'].append(stock.get('stock_exchange').get('currency'))
        stocks['exchange_country'].append(stock.get('stock_exchange').get('country'))
        stocks['exchange_city'].append(stock.get('stock_exchange').get('city'))
        stocks['exchange_website'].append(stock.get('stock_exchange').get('website'))

    offset += 1000
    params = {
        'limit': 1000,
        'offset': offset,
        'access_key': api_key,
    }
    res = requests.get(url, params)

stocks_df = pd.DataFrame(stocks)
stocks_df.to_excel(stocks_filename)
print('\nprocessing completed')
