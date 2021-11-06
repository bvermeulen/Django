from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from howdimain.utils.plogger import Logger
from stock.module_stock import TradingData

logger = Logger.getlogger()


@method_decorator(login_required, name='dispatch')
class NewsView(View):

    template_name = 'finance/stock_news.html'
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request, source, symbol):
        context = {
            'source': source,
            'symbol': symbol,
        }
        return render(request, self.template_name, context)

    def post(self, request, source, symbol):
        context = {
            'source': source,
            'symbol': symbol,
        }
        return render(request, self.template_name, context)