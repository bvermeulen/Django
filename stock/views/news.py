from django.shortcuts import render
from django.views.generic import View
from howdimain.utils.plogger import Logger
from stock.module_stock import TradingData

logger = Logger.getlogger()


class StockNewsView(View):

    template_name = 'finance/stock_news.html'
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request, source, symbol):
        stock_news = self.td.get_stock_news(symbol)
        context = {
            'source': source,
            'symbol': symbol,
            'company': self.td.get_company_name(symbol),
            'stock_news': stock_news,
        }
        return render(request, self.template_name, context)


class StockPressView(View):

    template_name = 'finance/stock_press.html'
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request, source, symbol):
        stock_press = self.td.get_stock_press(symbol)
        context = {
            'source': source,
            'symbol': symbol,
            'company': self.td.get_company_name(symbol),
            'stock_press': stock_press,
        }
        return render(request, self.template_name, context)
