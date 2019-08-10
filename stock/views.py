import json
import requests
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .models import Exchange, Stock
from .module_stock import WorldTradingData
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries
from howdimain.utils.min_max import get_min, get_max
from .stock_lists import indexes

from .test_data import chart_js_test
from pprint import pprint

font_red = '#FF3333'
font_green = 'green'
font_white = 'white'
font_weight = 'bolder'
font_size = '16'

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
            if quote_string.upper() in indexes:
                symbols =indexes.get(quote_string.upper())[0:20]
                stock_info = self.wtd.get_stock_trade_info(symbols)
                symbols =indexes.get(quote_string.upper())[20:40]
                stock_info += self.wtd.get_stock_trade_info(symbols)

            else:
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

        if not Stock.objects.filter(symbol=symbol):
            return redirect(reverse('stock_quote'))

        intraday_trades = self.wtd.get_stock_intraday_info(symbol)

        chart_data = []
        min_price,  max_price, max_volume = [None] * 3
        for trade in intraday_trades:
            chart_data.append([
                trade.time.strftime('%d-%m-%Y %H:%M'),
                trade.open, trade.close, trade.low, trade.high, trade.volume,
                ])
            min_price = get_min(trade.low, min_price)
            max_price = get_max(trade.high, max_price)
            max_volume = get_max(trade.volume, max_volume)

        if not min_price or not max_price or not max_volume:
            min_price, max_price, max_volume = [0] * 3

        schema = json.dumps(self.wtd.schema)
        chart_data = json.dumps(chart_data)

        try:
            initial_open = intraday_trades[1].open
            latest_close = intraday_trades[-2].close
            prc_change = 100 * (float(latest_close) -
                                float(initial_open)) / float(initial_open)

        except IndexError:
            initial_open, latest_close, prc_change = [None] * 3

        if initial_open and latest_close and prc_change:
            if abs(float(prc_change)) < 0.01:
                txt_color = 'txt_normal'
                caret = self.wtd.rectangle
            elif float(prc_change) < 0:
                txt_color = 'txt_red'
                caret = self.wtd.down_triangle
            else:
                txt_color = 'txt_green'
                caret = self.wtd.up_triangle

            subcaption = ''.join([Stock.objects.get(symbol=symbol).currency.currency,
                                  f' {float(latest_close):.2f} ({prc_change:.1f}%)',
                                  f' {caret}'])
        else:
            subcaption = ''

        caption = ''.join([Stock.objects.get(symbol=symbol).company,
                           ' (', symbol, ')' ])

        time_series = TimeSeries(FusionTable(schema, chart_data))
        time_series.AddAttribute('styleDefinition',
            {'txt_red': {'fill': font_red, 'font-weight': font_weight, 'font-size': font_size},
             'txt_green': {'fill': font_green, 'font-weight': font_weight, 'font-size': font_size},
             'txt_normal': {'fill': font_white, 'font-weight': font_weight, 'font-size': font_size}})

        time_series.AddAttribute('chart', {'multicanvas': '0', 'theme': 'candy', 'showlegend': '0',})
        time_series.AddAttribute('caption', {'text': caption, })
        time_series.AddAttribute('subcaption', {'text': subcaption, 'style': {'text': txt_color}, })
        time_series.AddAttribute('navigator', {'enabled': '0'})
        time_series.AddAttribute('extensions', {'customrangeselector': {'enabled': '0'}})
        time_series.AddAttribute('yaxis', [
            {'plot': [{'value':{'open':'open','high':'high','low':'low','close':'close'},
                       'type':'candlestick'}],
                     'title':'Stock Value',
                     'min': min_price*0.99,
                     'max': max_price*1.01,
                      },
            {'plot': [{'value': 'volume',
                       'type': 'column'}],
                     'title': 'Volume',
                     'max': max_volume * 3,
                      },
            ])

        trade_line = FusionCharts('timeseries',
                                  'trades',
                                  '700', '400',
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
