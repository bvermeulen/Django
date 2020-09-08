''' extract Financialmodelingprep exchanges and stocks
'''
import pandas as pd
import requests
from decouple import config


base_url = 'https://financialmodelingprep.com/api/v3/stock/'
api_key = config('API_token')
exchanges_filename = 'fmp_exchanges.xlsx'
tickers_filename = 'fmp_stocks.xlsx'

# extract exchanges
url = base_url + 'list'
params = {
    'apikey': api_key,
}

res = requests.get(url, params)

# extract exchanges
tickers = {
    'symbol': [],
    'name': [],
    'exchange': [],
}

exchanges = set()
for i, ticker in enumerate(res.json()):
    print(i, ticker)
    print(f'\rProcessing page {i:4} - {ticker["symbol"]} ...', end='')

    tickers['symbol'].append(ticker.get('symbol', 'N/A'))
    tickers['name'].append(ticker.get('name', 'N/A'))
    tickers['exchange'].append(ticker.get('exchange', 'N/A'))
    exchanges.add(ticker.get('exchange', 'N/A'))

exchange_df = pd.DataFrame({'exchange': list(exchanges)})
exchange_df.to_excel(exchanges_filename)

stocks_df = pd.DataFrame(tickers)
stocks_df.to_excel(tickers_filename)
print('\nprocessing completed')
