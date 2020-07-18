import requests
import pandas as pd
from decouple import config


fmp_url = 'https://financialmodelingprep.com/api/v3/quotes/index/'
params = {'apikey': config('API_token')}
excel_stocks_filename = 'fmp_indiceslisting.xlsx'

res = requests.get(fmp_url, params=params)
stock_list = res.json()

stock_dict = {
    'symbol': [],
    'name': [],
    'price': [],
    'exchange': [],
}
exchanges = set()
for stock in stock_list:
    stock_dict['symbol'].append(stock.get('symbol'))
    stock_dict['name'].append(stock.get('name'))
    stock_dict['price'].append(stock.get('price'))
    exchange = stock.get('exchange')
    stock_dict['exchange'].append(exchange)
    exchanges.add(exchange)

writer = pd.ExcelWriter(excel_stocks_filename)
stock_df = pd.DataFrame(stock_dict)
stock_df.to_excel(writer)
writer.save()
