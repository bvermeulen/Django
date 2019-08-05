from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .models import Exchange
from .module_stock import WorldTradingData


class QuoteView(View):
    model = Exchange
    form_class = StockQuoteForm
    template_name = 'stock/stock_quote.html'

    wtd = WorldTradingData()
    wtd.setup()
    markets = ['NASDAQ', 'NYSE', 'AEX']

    data_provider_url = 'www.worldtradingdata.com'

    def get(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': markets})
        context = {'stock_info': [],
                   'form': form,
                   'data_provider_url': self.data_provider_url,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)

        form = self.form_class(request.POST)
        if form.is_valid():
            quote_string = form.cleaned_data.get('quote_string')
            markets = form.cleaned_data.get('markets')
            symbols = self.wtd.parse_stock_name(
                quote_string,
                markets=markets)

            stock_info = self.wtd.get_stock_trade_info(symbols)
            request.session['quote_string'] = quote_string
            request.session['markets'] = markets

        else:
            stock_info = []

        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': markets})
        context = {'stock_info': stock_info,
                   'form': form,
                   'data_provider_url': self.data_provider_url,
        }

        return render(request, self.template_name, context)
