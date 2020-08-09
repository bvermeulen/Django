''' extract Marketstack exchanges and stocks
'''
import pandas as pd
import requests
from decouple import config


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
    'name': [],
    'acronym': [],
    'mic': [],
    'country': [],
    'country_code': [],
    'city': [],
    'website': [],
    'timezone': [],
    'currency': []
}

for exchange in res.json().get('data'):
    exchanges['name'].append(exchange.get('name'))
    exchanges['acronym'].append(exchange.get('acronym'))
    exchanges['mic'].append(exchange.get('mic'))
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
    'name': [],
    'symbol': [],
    'has_intraday': [],
    'has_eod': [],
    'exchange_name': [],
    'exchange_acronym': [],
    'exchange_mic': [],
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
        stocks['name'].append(stock.get('name'))
        stocks['symbol'].append(stock.get('symbol'))
        stocks['has_intraday'].append(stock.get('has_intraday'))
        stocks['has_eod'].append(stock.get('has_eod'))
        stocks['exchange_name'].append(stock.get('stock_exchange').get('name'))
        stocks['exchange_acronym'].append(stock.get('stock_exchange').get('acronym'))
        stocks['exchange_mic'].append(stock.get('stock_exchange').get('mic'))
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
