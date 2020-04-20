import datetime
import json
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from stock.models import Stock
from stock.module_stock import WorldTradingData
from howdimain.utils.min_max import get_min, get_max
from howdimain.utils.get_ip import get_client_ip
from howdimain.howdimain_vars import CARET_UP, CARET_DOWN, CARET_NO_CHANGE
from howdimain.utils.fusioncharts import FusionCharts, FusionTable, TimeSeries
from howdimain.utils.plogger import Logger


font_red = 'red'  #  '#FF3333'
font_green = 'green'
font_white = 'white'
font_weight = 'bolder'
font_size = '14'
chart_theme = 'candy'  #  other selection is fusion see www.fusioncharts.com
# todo: small sreen below values large screen reduce
height = '400'
width = '100%'
periods = ['max', '5', '3', '1']

logger = Logger.getlogger()
source = None


class IntraDayView(View):
    template_name = 'finance/stock_intraday.html'

    wtd = WorldTradingData()
    wtd.setup()
    data_provider_url = wtd.data_provider_url

    def get(self, request, source, symbol):

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

        if not min_price or not max_price:
            min_price, max_price = 0, 0

        if not max_volume:
            max_volume = 0

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
                caret = CARET_NO_CHANGE
            elif float(prc_change) < 0:
                txt_color = 'txt_red'
                caret = CARET_DOWN
            else:
                txt_color = 'txt_green'
                caret = CARET_UP

            subcaption = ''.join([Stock.objects.get(symbol=symbol).currency.currency,
                                  f' {float(latest_close):.2f} ({prc_change:.1f}%)',
                                  f' {caret}'])
        else:
            subcaption = ''
            txt_color = 'txt_normal'

        caption = ''.join([Stock.objects.get(symbol=symbol).company,
                           ' (', symbol, ')'])

        schema = json.dumps(self.wtd.get_schema(date_format))
        chart_data = json.dumps(chart_data)
        time_series = TimeSeries(FusionTable(schema, chart_data))

        time_series.AddAttribute(
            'styleDefinition',
            {'txt_red': {
                'fill': font_red, 'font-weight': font_weight, 'font-size': font_size},
             'txt_green': {
                 'fill': font_green, 'font-weight': font_weight, 'font-size': font_size},
             'txt_normal': {
                 'fill': font_white, 'font-weight': font_weight, 'font-size': font_size},
            })
        time_series.AddAttribute(
            'chart', {'multicanvas': '0', 'theme': chart_theme, 'showlegend': '0',})
        time_series.AddAttribute('caption', {'text': caption, })
        time_series.AddAttribute(
            'subcaption', {'text': subcaption, 'style': {'text': txt_color}, })
        time_series.AddAttribute('navigator', {'enabled': '0'})
        time_series.AddAttribute(
            'extensions', {'customrangeselector': {'enabled': '0'}})
        time_series.AddAttribute(
            'yaxis', [
                {'plot': [
                    {'value': {
                        'open':'open', 'high': 'high', 'low':'low', 'close':'close'},
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
                   'source': source,
                  }

        logger.info(f'user {request.user} [ip: {get_client_ip(request)}] is looking '
                    f'intraday trades for {symbol}')
        return render(request, self.template_name, context)

    def post(self, request, source, symbol):
        pass


class HistoryView(View):
    template_name = 'finance/stock_history.html'

    wtd = WorldTradingData()
    wtd.setup()
    data_provider_url = 'www.worldtradingdata.com'

    def get(self, request, source, symbol, period):

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
        min_price, max_price, max_volume = None, None, None
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

        if not min_price or not max_price:
            min_price, max_price = 0, 0
            start_date, end_date = '01-01-1900', '01-01-1900'

        else:
            end_date = history_trades[0].date
            start_date = end_date - datetime.timedelta(days=365)
            start_date = start_date.strftime(date_format)
            end_date = end_date.strftime(date_format)

        if not max_volume:
            max_volume = 0

        subcaption = ''
        caption = ''.join([Stock.objects.get(symbol=symbol).company,
                           ' (', symbol, ')'])

        schema = json.dumps(self.wtd.get_schema(date_format))
        chart_data = json.dumps(chart_data)
        time_series = TimeSeries(FusionTable(schema, chart_data))
        time_series.AddAttribute('chart', {
            'multicanvas': '0', 'theme': chart_theme, 'showlegend': '0',})
        time_series.AddAttribute('caption', {'text': caption, })
        time_series.AddAttribute('subcaption', {'text': subcaption,})
        time_series.AddAttribute('navigator', {'enabled': '1'}, )
        time_series.AddAttribute('extensions', {'customrangeselector': {'enabled': '1'}})
        time_series.AddAttribute('xaxis', {
            'initialinterval': {'from': start_date, 'to': end_date}})
        time_series.AddAttribute('yaxis', [
            {'plot': [{'value':{
                'open':'open', 'high':'high', 'low': 'low', 'close': 'close'},
                       'type': 'candlestick'}],
             'title': 'Stock Value (' + Stock.objects.get(symbol=symbol).
                      currency.currency + ')',
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
                   'source': source,
                  }

        logger.info(f'user {request.user} [ip: {get_client_ip(request)}] is looking '
                    f'historic trades for {symbol}')
        return render(request, self.template_name, context)

    def post(self, request, source, symbol, period):
        pass
