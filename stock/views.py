import json
import requests
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .models import Exchange, Stock
from .module_stock import WorldTradingData
from collections import OrderedDict
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries


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

        schema = [{'name': 'Time',
                   'type': 'date',
                   'format': '%d-%m-%Y %-I:%-M',
                  },
                  {'name': 'Price',
                   'type': 'number',
                  }]

        chart_data = []
        _min = None; _max = None
        for trade in intraday_trades:
            chart_data.append([
                trade.time.strftime('%d-%m-%Y %H:%M'),
                trade.price
                ])

            if trade.price:
                if _min is None:
                    _min = float(trade.price)
                elif float(trade.price) < _min:
                    _min = float(trade.price)

                if _max is None:
                    _max = float(trade.price)
                elif float(trade.price) >= _max:
                    _max = float(trade.price)

        schema = json.dumps(schema)
        chart_data = json.dumps(chart_data)

        caption = ''.join([Stock.objects.filter(symbol=symbol).first().company,' (', symbol,')'])
        try:
            date_subcaption = intraday_trades[0].time.strftime('%d %B %Y')
            date_interval = intraday_trades[0].time.strftime('%d-%m-%Y')
        except IndexError:
            date_subcaption = ''
            date_interval = ''

        time_series = TimeSeries(FusionTable(schema, chart_data))
        time_series.AddAttribute('caption', {'text': f'{caption}'})
        time_series.AddAttribute('subcaption', {'text': f'{date_subcaption}'})
        time_series.AddAttribute('navigator', {'enabled': 0})
        time_series.AddAttribute('chart', {'showlegend': 0})
        time_series.AddAttribute('extensions', {'customRangeSelector': {'enabled': 0}})
        if _min and _max:
            time_series.AddAttribute('yaxis', {'min': _min*0.99, 'max': _max*1.01})
        time_series.AddAttribute('xaxis', {'initialInterval': {'from': f'{date_interval} 10:00', 'to': f'{date_interval} 15:00'}})

        trade_line = FusionCharts('timeseries',
                                  'trades',
                                  '600', '400',
                                  'chart-container',
                                  'json',
                                  time_series,
                                 )

        context = {'chart_js': trade_line.render(),
                   'data_provider_url': self.data_provider_url,
        }

        return render(request, self.template_name, context)

    def post(self, request, symbol):
        pass
