
from django.shortcuts import render
from django.views.generic import View
from stock.forms import StockQuoteForm
from stock.models import Person, Portfolio
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
    markets = ['XNAS', 'XNYS', 'XAMS', 'INDEX']
    data_provider_url = td.data_provider_url

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            # add Person class to user
            user.__class__ = Person

        try:
            default_user = Person.objects.get(username='default_user')

        except Person.DoesNotExist:
            default_user = None

        quote_string = request.session.get('quote_string', '')
        markets = request.session.get('markets', self.markets)
        form = self.form_class(initial={'quote_string': quote_string,
                                        'markets': markets, })

        portfolios = default_user.get_portfolio_names()

        if user.is_authenticated:
            portfolios += user.get_portfolio_names()

        context = {'source': source,
                   'stock_info': [],
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        # add Person class to user
        if user.is_authenticated:
            user.__class__ = Person

        try:
            default_user = Person.objects.get(username='default_user')

        except Person.DoesNotExist:
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
                    # try if user has selected a portfolio if authenticated
                    if user.is_authenticated:
                        symbols = Portfolio.objects.get(
                            user=user, portfolio_name=selected_portfolio).get_stock()
                        stock_info = self.td.get_stock_trade_info(symbols[0:20])
                        stock_info += self.td.get_stock_trade_info(symbols[20:40])

                    else:
                        raise Portfolio.DoesNotExist

                except Portfolio.DoesNotExist:
                    # try if it is a default portfolio
                    try:
                        symbols = Portfolio.objects.get(
                            user=default_user, portfolio_name=selected_portfolio).get_stock()  #pylint: disable=line-too-long
                        stock_info = self.td.get_stock_trade_info(symbols[0:20])
                        stock_info += self.td.get_stock_trade_info(symbols[20:40])

                    except Portfolio.DoesNotExist:
                        pass

            else:
                symbols = self.td.parse_stock_quote(quote_string, markets=markets)
                stock_info = self.td.get_stock_trade_info(symbols[0:20])

            request.session['quote_string'] = quote_string
            request.session['markets'] = markets
            logger.info(f'user {user} [ip: {get_client_ip(request)}] looking '
                        f'up: {quote_string} / {selected_portfolio}')

        else:
            stock_info = []

        portfolios = default_user.get_portfolio_names()

        if user.is_authenticated:
            portfolios += user.get_portfolio_names()

        stock_info = add_display_tokens(stock_info)
        stock_info = format_and_sort_stocks(stock_info)
        context = {'source': source,
                   'stock_info': stock_info,
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)
