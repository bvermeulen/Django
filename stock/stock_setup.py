from stock.models import Stock, Portfolio, StockSelection
from django.contrib.auth.models import User
bruno = User.objects.get(username='bvermeulen')
john = User.objects.get(username='johndean121')
apple = Stock.objects.get(symbol='AAPL')
slb = Stock.objects.get(symbol='SLB')
bpf = Portfolio.objects.get(portfolio_name='AMS', user=bruno)

from stock.models import Stock, Portfolio, StockSelection
from stock import module_stock as ms
wtd = ms.WorldTradingData()
wtd.setup()
exchanges = ['NYSE', 'NASDAQ', 'AEX', 'LSE']
symbols = wtd.parse_stock_name('Schlu', markets=exchanges)
wtd.stock_intraday_info('AMZN')

import requests
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries
data = requests.get('https://s3.eu-central-1.amazonaws.com/fusion.store/ft/data/stock-chart-with-volume_data.json').text
schema = requests.get('https://s3.eu-central-1.amazonaws.com/fusion.store/ft/schema/stock-chart-with-volume_schema.json').text
fusionTable = FusionTable(schema, data)
timeSeries = TimeSeries(fusionTable)
timeSeries.AddAttribute('caption', '{"text":"Apple Inc. Stock Price"}')
timeSeries.AddAttribute('subcaption', '{"text":"Stock prices from May 2014 - November 2018"}')
timeSeries.AddAttribute('chart', '{"exportenabled":1,"multicanvas":false,"theme":"candy"}')
timeSeries.AddAttribute('yaxis', '[{"plot":[{"value":{"open":"Open","high":"High","low":"Low","close":"Close"},"type":"candlestick"}],"format":{"prefix":"$"},"title":"Stock Price"},{"plot":[{"value":"Volume","type":"column"}],"max":"900000000"}]')
timeSeries.AddAttribute('navigator', '{"enabled":0}')
fcChart = FusionCharts("timeseries", "ex1", 700, 450, "chart-1", "json", timeSeries)
