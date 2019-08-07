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
