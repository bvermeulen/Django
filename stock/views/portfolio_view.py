from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from stock.forms import PortfolioForm
from stock.models import Exchange, Stock, Portfolio, StockSelection
from stock.module_stock import WorldTradingData
from howdimain.utils.plogger import Logger
import json

logger = Logger.getlogger()

from pprint import pprint

@method_decorator(login_required, name='dispatch')
class PortfolioView(View):

    form_class = PortfolioForm
    template_name = 'finance/portfolio.html'
    wtd = WorldTradingData()

    def get(self, request):
        symbol = ''
        currency = request.session.get('currency', 'EUR')

        form = self.form_class(
            user=request.user,
            initial={'symbol': symbol,
                     'currency': currency})

        context = {'form': form, }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        form = self.form_class(request.POST, user=user)
        if form.is_valid():
            form_data = form.cleaned_data
            selected_portfolio = form_data.get('portfolios')
            portfolio_name = form_data.get('portfolio_name')
            new_portfolio = form_data.get('new_portfolio')
            symbol = form_data.get('symbol')
            currency = form_data.get('currency')
            btn1_pressed = form_data.get('btn1_pressed')
            btn2_pressed = form_data.get('btn2_pressed')
            quantity = form_data.get('quantity')
            previous_selected = request.session.get('selected')

            # TODO check input names for portfolio name, symbol and new_portfolio
            try:
                portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=selected_portfolio)

            except Portfolio.DoesNotExist:
                portfolio = None
                get_stock = 'empty'

            if previous_selected != selected_portfolio:
                get_stock = 'yes'
            else:
                get_stock = 'no'

            # create new portfolio
            if new_portfolio != '':
                try:
                    portfolio = Portfolio.objects.create(
                        user=user, portfolio_name=new_portfolio)
                    selected_portfolio = new_portfolio
                    get_stock = 'empty'

                except IntegrityError:
                    print('cannot create portfolio')
                    get_stock = 'no'

            # rename or delete portfolio
            if (portfolio and btn1_pressed == 'rename_portfolio'
                and portfolio_name != selected_portfolio):

                get_stock = 'no'
                try:
                    portfolio.portfolio_name = portfolio_name
                    portfolio.save()
                    selected_portfolio = portfolio_name

                except IntegrityError:
                    pass

            if portfolio and btn1_pressed == 'delete_portfolio':
                portfolio.delete()
                selected_portfolio = ''
                get_stock = 'empty'

            # add stock to portfolio
            if portfolio and btn1_pressed == 'add_new_symbol':
                try:
                    StockSelection.objects.create(
                        stock=Stock.objects.get(symbol=symbol),
                        quantity=0,
                        portfolio=portfolio)
                    symbol = ''
                    get_stock = 'yes'

                except (Stock.DoesNotExist, IntegrityError):
                    get_stock = 'no'

            # change quantity or delete stock in portfolio
            if portfolio and btn2_pressed and quantity:
                try:
                    stock = portfolio.stocks.get(stock__symbol=btn2_pressed)
                    stock.quantity = float(quantity)
                    stock.save()
                    get_stock = 'yes'

                except (TypeError, ValueError):
                    get_stock = 'no'

            elif portfolio and btn2_pressed and not quantity:
                portfolio.stocks.get(stock__symbol=btn2_pressed).delete()
                get_stock = 'yes'

            else:
                pass

            # get stock info
            if get_stock == 'yes':
                print('get stock')
                stocks = self.wtd.get_portfolio_stock_info(portfolio)

            elif get_stock == 'no':
                stocks = json.loads(request.session.get('stock_info'))

            elif get_stock == 'empty':
                stocks = []

            else:
                assert False, f'invalid selection for get_stock: {get_stock}'

            request.session['stock_info'] = json.dumps(stocks, cls=DjangoJSONEncoder)
            request.session['selected'] = selected_portfolio
            form = self.form_class(
                user=request.user,
                initial={'portfolio_name': selected_portfolio,
                         'portfolios': selected_portfolio,
                         'symbol': symbol,
                         'currency': currency})

        else:
            form = self.form_class(
                user=request.user,
                initial={'portfolio_name': '',
                         'symbol': '',
                         'currency': 'EUR'})

            stocks = []

        context = {'form': form,
                   'stocks': stocks}
        return render(request, self.template_name, context)
