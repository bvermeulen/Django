import json
import requests
import datetime
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from .forms import StockQuoteForm
from .models import Exchange, Stock, Portfolio
from .module_stock import WorldTradingData
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries
from howdimain.utils.plogger import Logger
from howdimain.utils.min_max import get_min, get_max


font_red = 'red'  #  '#FF3333'
font_green = 'green'
font_white = 'white'
font_weight = 'bolder'
font_size = '14'
chart_theme = 'candy'  #  other selection is fusion see www.fusioncharts.com
height = 400
width = 700
periods = ['max', '5', '3', '1']

logger = Logger.getlogger()

class QuoteView(View):
    form_class = StockQuoteForm
    template_name = 'finance/stock_quotes.html'

    wtd = WorldTradingData()
    wtd.setup()
    markets = ['NASDAQ', 'NYSE', 'AEX']
    data_provider_url = 'www.worldtradingdata.com'
    default_user = User.objects.get(username='default_user')

    def get(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': markets, })

        portfolios = [item.portfolio_name for item in Portfolio.objects.filter(
            user=self.default_user)]
        print(portfolios)
        context = {'stock_info': [],
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)

    def post(self, request):
        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)

        form = self.form_class(request.POST)
        if form.is_valid():
            quote_string = form.cleaned_data.get('quote_string')
            selected_portfolio = form.cleaned_data.get('selected_portfolio')
            markets = form.cleaned_data.get('markets')

            try:
                symbols = []
                default_portfolio = Portfolio.objects.filter(
                    user=self.default_user, portfolio_name=selected_portfolio)
                for stock in default_portfolio.first().stocks.all():
                    symbols.append(stock.stock.symbol)
                stock_info = self.wtd.get_stock_trade_info(symbols[0:20])
                stock_info += self.wtd.get_stock_trade_info(symbols[20:40])

            except AttributeError:
                symbols = self.wtd.parse_stock_name(quote_string, markets=markets)
                stock_info = self.wtd.get_stock_trade_info(symbols[0:20])

            request.session['quote_string'] = quote_string
            request.session['markets'] = markets

            logger.info(f'user {request.user} looking up: {quote_string}')

        else:
            stock_info = []

        portfolios = [item.portfolio_name for item in Portfolio.objects.filter(
            user=self.default_user)]
        context = {'stock_info': stock_info,
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)


class IntraDayView(View):
    template_name = 'finance/stock_intraday.html'

    wtd = WorldTradingData()
    wtd.setup()
    data_provider_url = 'www.worldtradingdata.com'

    def get(self, request, symbol):

        if not Stock.objects.filter(symbol=symbol):
            return redirect(reverse('stock_quotes'))

        intraday_trades = self.wtd.get_stock_intraday_info(symbol)
        chart_data = []
        min_price, max_price, max_volume = None, None, None
        date_format = '%d-%m-%Y %H:%M'

        for trade in intraday_trades:
            chart_data.append([
                trade.date.strftime(date_format),
                trade.open, trade.close, trade.low, trade.high,
                trade.volume, ])

            min_price = get_min(trade.low, min_price)
            max_price = get_max(trade.high, max_price)
            max_volume = get_max(trade.volume, max_volume)

        if not min_price or not max_price or not max_volume:
            min_price, max_price, max_volume = 0, 0, 0

        try:
            initial_open = intraday_trades[1].open
            latest_close = intraday_trades[-2].close
            prc_change = 100 * (float(latest_close) -
                                float(initial_open)) / float(initial_open)

        except IndexError:
            initial_open, latest_close, prc_change = None, None, None

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
            txt_color = 'txt_normal'

        caption = ''.join([Stock.objects.get(symbol=symbol).company,
                           ' (', symbol, ')' ])

        schema = json.dumps(self.wtd.get_schema(date_format))
        chart_data = json.dumps(chart_data)
        time_series = TimeSeries(FusionTable(schema, chart_data))

        time_series.AddAttribute('styleDefinition',
            {'txt_red': {'fill': font_red, 'font-weight': font_weight, 'font-size': font_size},
             'txt_green': {'fill': font_green, 'font-weight': font_weight, 'font-size': font_size},
             'txt_normal': {'fill': font_white, 'font-weight': font_weight, 'font-size': font_size},
        })
        time_series.AddAttribute('chart', {'multicanvas': '0', 'theme': chart_theme, 'showlegend': '0',})
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
            {'plot': [{'value': 'volume', 'type': 'column'}],
                     'title': 'Volume',
                     'max': max_volume * 3,
            },
        ])

        trade_series = FusionCharts('timeseries',
                                    'trades',
                                    width, height,
                                    'chart-container',
                                    'json',
                                    time_series,
        )

        context = {'chart_js': trade_series.render(),
                   'data_provider_url': self.data_provider_url,
                   'stock_symbol': symbol,
        }

        logger.info(f'user {request.user} is looking intraday trades for {symbol}')
        return render(request, self.template_name, context)

    def post(self, request, symbol):
        pass


class HistoryView(View):
    template_name = 'finance/stock_history.html'

    wtd = WorldTradingData()
    wtd.setup()
    data_provider_url = 'www.worldtradingdata.com'

    def get(self, request, symbol, period):

        if period not in periods:
            return redirect(reverse('stock_quotes'))
        elif period == 'max':
            period = '1000'

        if not Stock.objects.filter(symbol=symbol):
            return redirect(reverse('stock_quotes'))

        history_trades = self.wtd.get_stock_history_info(symbol)
        if history_trades:
            start_period = history_trades[0].date -\
                           datetime.timedelta(days=int(period) * 365)

        chart_data = []
        min_price,  max_price, max_volume = None, None, None
        date_format = '%d-%m-%Y'
        for trade in history_trades:
            if trade.date > start_period:
                chart_data.append([
                    trade.date.strftime(date_format),
                    trade.open, trade.close, trade.low, trade.high,
                    trade.volume,])

                min_price = get_min(trade.low, min_price)
                max_price = get_max(trade.high, max_price)
                max_volume = get_max(trade.volume, max_volume)

        if not min_price or not max_price or not max_volume:
            min_price, max_price, max_volume = 0, 0, 0
            start_date, end_date = '01-01-1900', '01-01-1900'
        else:
            end_date = history_trades[0].date
            start_date = end_date - datetime.timedelta(days=365)
            start_date = start_date.strftime(date_format)
            end_date = end_date.strftime(date_format)

        subcaption = ''
        caption = ''.join([Stock.objects.get(symbol=symbol).company,
                           ' (', symbol, ')' ])

        schema = json.dumps(self.wtd.get_schema(date_format))
        chart_data = json.dumps(chart_data)
        time_series = TimeSeries(FusionTable(schema, chart_data))
        time_series.AddAttribute('chart', {'multicanvas': '0', 'theme': chart_theme, 'showlegend': '0',})
        time_series.AddAttribute('caption', {'text': caption, })
        time_series.AddAttribute('subcaption', {'text': subcaption,})
        time_series.AddAttribute('navigator', {'enabled': '1'}, )
        time_series.AddAttribute('extensions', {'customrangeselector': {'enabled': '1'}})
        time_series.AddAttribute('xaxis', {'initialinterval': {'from': start_date, 'to': end_date}})
        time_series.AddAttribute('yaxis', [
            {'plot': [{'value':{'open':'open','high':'high','low':'low','close':'close'},
                       'type':'candlestick'}],
                     'title':'Stock Value (' + Stock.objects.get(symbol=symbol).currency.currency + ')',
                     'min': min_price*0.99,
                     'max': max_price*1.01,
            },
            {'plot': [{'value': 'volume', 'type': 'column'}],
                     'title': 'Volume',
                     'max': max_volume * 3,
            },
        ])

        trade_series = FusionCharts('timeseries',
                                    'trades',
                                    width, height,
                                    'chart-container',
                                    'json',
                                    time_series,
        )

        context = {'chart_js': trade_series.render(),
                   'data_provider_url': self.data_provider_url,
                   'stock_symbol': symbol,
        }

        logger.info(f'user {request.user} is looking historic trades for {symbol}')
        return render(request, self.template_name, context)

    def post(self, request, symbol, period):
        pass
