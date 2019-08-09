import json
import requests
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .models import Exchange, Stock
from .module_stock import WorldTradingData
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries
from howdimain.utils.min_max import get_min, get_max

from pprint import pprint


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

class IntraDayView(View):
    template_name = 'stock/stock_intraday.html'

    wtd = WorldTradingData()
    wtd.setup()
    data_provider_url = 'www.worldtradingdata.com'

    def get(self, request, symbol):

        intraday_trades = self.wtd.get_stock_intraday_info(symbol)

        chart_data = []
        min_price = None; max_price = None; max_volume = None
        for trade in intraday_trades:
            chart_data.append([
                trade.time.strftime('%d-%m-%Y %H:%M'),
                trade.open, trade.close, trade.low, trade.high, trade.volume,
                ])
            min_price = get_min(trade.low, min_price)
            max_price = get_max(trade.high, max_price)
            max_volume = get_max(trade.volume, max_volume)

        if not min_price or not max_price or not max_volume:
            min_price = 0
            max_price = 0
            max_volume = 0

        schema = json.dumps(self.wtd.schema)
        chart_data = json.dumps(chart_data)

        caption = ''.join([Stock.objects.filter(symbol=symbol).first().company,' (', symbol,')'])
        try:
            date_subcaption = intraday_trades[0].time.strftime('%d %B %Y')
            date_interval = intraday_trades[0].time.strftime('%d-%m-%Y')
        except IndexError:
            date_subcaption = ''
            date_interval = ''

        time_series = TimeSeries(FusionTable(schema, chart_data))
        time_series.AddAttribute('chart', "{'multicanvas': false, 'theme': 'candy', 'showlegend': 0}")
        time_series.AddAttribute('caption', {'text': f'{caption}'})
        time_series.AddAttribute('subcaption', {'text': f'{date_subcaption}'})
        time_series.AddAttribute('navigator', {'enabled': 0})
        time_series.AddAttribute('extensions', {'customRangeSelector': {'enabled': 0}})  # not working
        interval = "[{'initialinterval': {" + "'from': " + f"'{date_interval} 10:00', 'to': " + f"'{date_interval} 15:00'" + "}}]"
        time_series.attributes.append({'xaxis': interval})  # not working
        time_series.AddAttribute('yaxis', [
            {'plot': [{'value':{'open':'open','high':'high','low':'low','close':'close'},
                       'type':'candlestick'}],
                     'title':'Stock Value',
                     'min': min_price*0.99,
                     'max': max_price*1.01,
                      },
            {'plot': [{'value': 'volume',
                       'type': 'column'}],
                     'max': max_volume * 3,
                      },
            ])

        trade_line = FusionCharts('timeseries',
                                  'ex1',
                                  '700', '450',
                                  'chart-container',
                                  'json',
                                  time_series,
                                 )

        time_series.AddAttribute('extensions', {'customRangeSelector': {'enabled': 0}})

        context = {'chart_js': trade_line.render(),
                   'data_provider_url': self.data_provider_url,
        }

        return render(request, self.template_name, context)

    def post(self, request, symbol):
        pass
