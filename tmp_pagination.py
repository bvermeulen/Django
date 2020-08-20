from howdimain.utils.pagination_marketstack import pagination_marketstack, pagination_marketstack_threaded

url = 'https://api.marketstack.com/v1/eod'
token = '46aab4b2a0fe1576cc2fd0b34126259e'
symbol = '7203.XTKS'

series = pagination_marketstack_threaded(url, token, symbol, set_total=400)

print(series)
