
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.generic import View
from stock.forms import StockQuoteForm
from stock.models import Portfolio
from stock.module_stock import TradingData
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import add_display_tokens, format_and_sort_stocks
from howdimain.utils.plogger import Logger


logger = Logger.getlogger()
source = 'quotes'


class QuoteView(View):
    form_class = StockQuoteForm
    template_name = 'finance/stock_quotes.html'

    td = TradingData()
    td.setup()
    markets = ['NASDAQ', 'NYSE', 'AEX']
    data_provider_url = td.data_provider_url
    def get(self, request):
        user = request.user
        try:
            default_user = User.objects.get(username='default_user')
        except User.DoesNotExist:
            default_user = None

        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': markets, })

        portfolios = [item.portfolio_name for item in Portfolio.objects.filter(
            user=default_user)]

        if user.is_authenticated:
            portfolios += [item.portfolio_name for item in Portfolio.objects.filter(
                user=user)]

        context = {'source': source,
                   'stock_info': [],
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        try:
            default_user = User.objects.get(username='default_user')
        except User.DoesNotExist:
            default_user = None

        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)

        form = self.form_class(request.POST)
        if form.is_valid():
            quote_string = form.cleaned_data.get('quote_string')
            selected_portfolio = form.cleaned_data.get('selected_portfolio')
            markets = form.cleaned_data.get('markets')
            symbols = []
            stock_info = []

            if selected_portfolio:
                try:
                    # try if user has selected a portfolio
                    portfolio = Portfolio.objects.filter(
                        user=user, portfolio_name=selected_portfolio)

                    for stock in portfolio.first().stocks.all():
                        symbols.append(stock.stock.symbol)

                    stock_info = self.td.get_stock_trade_info(symbols[0:20])
                    stock_info += self.td.get_stock_trade_info(symbols[20:40])

                except (TypeError, AttributeError):
                    # try if it is a default portfolio
                    try:
                        portfolio = Portfolio.objects.filter(
                            user=default_user, portfolio_name=selected_portfolio)

                        for stock in portfolio.first().stocks.all():
                            symbols.append(stock.stock.symbol)

                        stock_info = self.td.get_stock_trade_info(symbols[0:20])
                        stock_info += self.td.get_stock_trade_info(symbols[20:40])

                    except AttributeError:
                        pass

            else:
                symbols = self.td.parse_stock_name(quote_string, markets=markets)
                stock_info = self.td.get_stock_trade_info(symbols[0:20])

            request.session['quote_string'] = quote_string
            request.session['markets'] = markets
            logger.info(f'user {request.user} [ip: {get_client_ip(request)}] looking '
                        f'up: {quote_string}  / {selected_portfolio}')

        else:
            stock_info = []

        portfolios = [item.portfolio_name for item in Portfolio.objects.filter(
            user=default_user)]

        if user.is_authenticated:
            portfolios += [item.portfolio_name for item in Portfolio.objects.filter(
                user=user)]

        stock_info = add_display_tokens(stock_info)
        stock_info = format_and_sort_stocks(stock_info)
        context = {'source': source,
                   'stock_info': stock_info,
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)
