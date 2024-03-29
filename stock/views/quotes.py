from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from stock.forms import StockQuoteForm
from stock.models import Person, Portfolio
from stock.module_stock import TradingData
from howdimain.howdimain_vars import STOCK_DETAILS
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import add_display_tokens, format_and_sort_stocks
from howdimain.utils.plogger import Logger


logger = Logger.getlogger()
source = 'quotes'


class QuoteView(View):
    stockquote_form = StockQuoteForm
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
        selected_portfolio = request.session.get('selected_portfolio', '')
        markets = request.session.get('markets', self.markets)
        stockdetail = request.session.get('stockdetail', STOCK_DETAILS[0][0])
        form = self.stockquote_form(initial={
            'quote_string': quote_string,
            'selected_portfolio': selected_portfolio,
            'markets': markets,
            'stockdetails': stockdetail,
        })
        portfolios = default_user.get_portfolio_names()

        if user.is_authenticated:
            portfolios += user.get_portfolio_names()

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

        stock_info = add_display_tokens(stock_info)
        stock_info = format_and_sort_stocks(stock_info)

        context = {'source': source,
                   'stock_info': stock_info,
                   'form': form,
                   'portfolios': sorted(portfolios),
                   'data_provider_url': self.data_provider_url, }

        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        quote_string = request.session.get('quote_string', '')
        selected_portfolio = request.session.get('selected_portfolio', '')
        markets = request.session.get('markets', self.markets)
        stockdetail = request.session.get('stockdetail', STOCK_DETAILS[0][0])

        form = self.stockquote_form(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            new_quote_string = form_data.get('quote_string')
            new_selected_portfolio = form_data.get('selected_portfolio')
            markets = form_data.get('markets')
            stockdetail = form_data.get('stockdetails')

            if new_selected_portfolio != selected_portfolio:
                selected_portfolio = new_selected_portfolio
                quote_string = ''

            elif new_quote_string != quote_string:
                quote_string = new_quote_string
                selected_portfolio = ''

            else:
                pass

            request.session['quote_string'] = quote_string
            request.session['selected_portfolio'] = selected_portfolio
            request.session['markets'] = markets
            request.session['stockdetail'] = stockdetail
            logger.info(f'user {user} [ip: {get_client_ip(request)}] looking '
                        f'up: {quote_string} / {selected_portfolio}')

        else:
            pass

        return redirect(reverse('stock_quotes'))
