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

    def get(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        market_objects = Exchange.objects.filter(exchange_short__in=markets)
        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': market_objects})
        context = {'stock_info': [],
                   'form': form,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        market_objects = Exchange.objects.filter(exchange_short__in=markets)

        form = self.form_class(request.POST)
        if form.is_valid():
            quote_string = form.cleaned_data.get('quote_string')
            market_objects = form.cleaned_data.get('markets')
            markets = [market.exchange_short for market in market_objects]
            symbols = self.wtd.parse_stock_name(
                quote_string,
                markets=markets)

            stock_info = self.wtd.get_stock_trade_info(symbols)
            request.session['quote_string'] = quote_string
            request.session['markets'] = markets

        else:
            stock_info = []

        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': market_objects})
        context = {'stock_info': stock_info,
                   'form': form,
        }

        return render(request, self.template_name, context)
