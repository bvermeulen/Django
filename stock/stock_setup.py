from stock.models import Stock, Portfolio, StockSelection
from stock.forms import PortfolioForm
from django.contrib.auth.models import User
from pprint import pprint
bruno = User.objects.get(username='bvermeulen')
john = User.objects.get(username='johndean121')
default = User.objects.get(username='default_user')
apple = Stock.objects.get(symbol='AAPL')
slb = Stock.objects.get(symbol='SLB')
portfolio = Portfolio.objects.get(portfolio_name='Techno', user=default)
f = PortfolioForm(user=default, initial={'selected_portfolio':'Techno'})
p = f['portfolios']
s = p[0]

from django.contrib.auth.models import User
from stock.models import Stock, Portfolio, StockSelection, Currency
from stock import module_stock as ms
from pprint import pprint
wtd = ms.WorldTradingData()
wtd.setup()
a = wtd.update_currencies()


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
