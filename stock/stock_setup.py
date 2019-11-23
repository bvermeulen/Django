from django.contrib.auth.models import User
from stock.models import Stock, Portfolio, StockSelection, Currency
from stock.forms import PortfolioForm
from django.contrib.auth.models import User
from stock import module_stock as ms
from pprint import pprint
bruno = User.objects.get(username='bvermeulen')
john = User.objects.get(username='johndean121')
default = User.objects.get(username='default_user')
apple = Stock.objects.get(symbol='AAPL')
slb = Stock.objects.get(symbol='SLB')
portfolio = Portfolio.objects.get(portfolio_name='Techno', user=default)
f = PortfolioForm(user=default, initial={'selected_portfolio':'Techno'})
wtd = ms.WorldTradingData()
wtd.setup()
stocks = wtd.get_portfolio_stock_info(portfolio)
wtd.calculate_stocks_value(stocks, 'EUR')

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

import stock.module_stock as ms
ps = ms.PopulateStock()
ps.read_csv('stock/stock info/worldtradingdata-stocklist.csv')
ps.symbols()
