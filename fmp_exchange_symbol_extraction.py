""" extract Financialmodelingprep exchanges and stocks
"""
import json
import pandas as pd
import requests
from decouple import config


base_url = "https://financialmodelingprep.com/api/v3/stock/"
api_key = config("API_token")
tickers_filename = "230828_fmp_stocks.xlsx"

# get the fmp exchange table
with open("fmp_exchange_table.json", "rt", encoding="utf-8") as jf:
    fmp_exchange_table = json.load(jf)

# extract stock
url = base_url + "list"
params = {
    "apikey": api_key,
}
res = requests.get(url, params)

tickers = {
    "symbol": [],
    "name": [],
    "exchange_mic": [],
    "exchange_fmp": [],
    "type": [],
}
for i, ticker in enumerate(res.json()):
    print(f'\rProcessing page {i:4} - {ticker["symbol"]:40} ...', end="")

    if exchange_fmp := ticker.get("exchange"):
        exchange_mic = fmp_exchange_table.get(exchange_fmp)

    else:
        exchange_mic = None

    tickers["symbol"].append(ticker.get("symbol", "N/A"))
    tickers["name"].append(ticker.get("name", "N/A"))
    tickers["type"].append(ticker.get("type", None))
    tickers["exchange_mic"].append(exchange_mic)
    tickers["exchange_fmp"].append(exchange_fmp)


stocks_df = pd.DataFrame(tickers)
stocks_df.to_excel(tickers_filename)
print("\nprocessing completed")
