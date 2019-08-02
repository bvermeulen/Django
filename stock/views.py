from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .module_stock import WorldTradingData
from pprint import pprint

class QuoteView(View):
    form_class = StockQuoteForm
    template_name = 'stock/stock_quote.html'

    wtd = WorldTradingData()
    wtd.setup()
    markets = ['NASDAQ', 'NYSE', 'AEX']

    def get(self, request):
        quote_string = request.session.get('quote_string','')
        form = self.form_class(initial={'quote_string': quote_string})
        context = {'stock_info': [],
                   'form': form,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            quote_string = form.cleaned_data.get('quote_string')
            symbols = self.wtd.parse_stock_name(
                quote_string,
                markets=self.markets)
            stock_info = self.wtd.get_stock_trade_info(symbols)
            request.session['quote_string'] = quote_string

        else:
            stock_info = []

        form = self.form_class(initial={'quote_string': quote_string})
        context = {'stock_info': stock_info,
                   'form': form,
        }

        return render(request, self.template_name, context)
