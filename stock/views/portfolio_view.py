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
        self.request = request
        self.user = self.request.user

        form = self.form_class(self.request.POST, user=self.user)
        if form.is_valid():
            form_data = form.cleaned_data
            self.selected_portfolio = form_data.get('portfolios')
            self.portfolio_name = form_data.get('portfolio_name')
            self.new_portfolio = form_data.get('new_portfolio')
            self.symbol = form_data.get('symbol')
            self.currency = form_data.get('currency')
            self.btn1_pressed = form_data.get('btn1_pressed')
            self.btn2_pressed = form_data.get('btn2_pressed')
            self.previous_selected = request.session.get('selected portfolio')

            try:
                self.portfolio = Portfolio.objects.get(
                    user=self.user, portfolio_name=self.selected_portfolio)

            except Portfolio.DoesNotExist:
                self.portfolio = None
                self.get_stock = 'empty'

            if self.previous_selected != self.selected_portfolio:
                self.get_stock = 'yes'
            else:
                self.get_stock = 'no'

            self.create_new_portfolio()
            self.rename_or_delete_portfololio_or_add_stock()
            self.change_quantity_or_delete_symbol()
            self.get_stock_info()

            request.session['stock_info'] = json.dumps(self.stocks, cls=DjangoJSONEncoder)
            request.session['selected portfolio'] = self.selected_portfolio
            form = self.form_class(
                user=self.user,
                initial={'portfolio_name': self.selected_portfolio,
                         'portfolios': self.selected_portfolio,
                         'symbol': self.symbol,
                         'currency': self.currency})

        else:
            form = self.form_class(
                user=self.user,
                initial={'portfolio_name': '',
                         'symbol': '',
                         'currency': 'EUR'})

            self.stocks = []

        context = {'form': form,
                   'stocks': self.stocks}
        return render(self.request, self.template_name, context)

    def create_new_portfolio(self):

        if self.new_portfolio != '':
            try:
                self.portfolio = Portfolio.objects.create(
                    user=self.user, portfolio_name=self.new_portfolio)
                self.selected_portfolio = self.new_portfolio
                self.get_stock = 'empty'

            except IntegrityError:
                print('cannot create portfolio')
                pass

    def rename_or_delete_portfololio_or_add_stock(self):

        if self.btn1_pressed:

            if self.portfolio and self.btn1_pressed == 'rename_portfolio':
                self.get_stock = 'no'
                if self.portfolio_name != self.selected_portfolio:

                    try:
                        self.portfolio.portfolio_name = self.portfolio_name
                        self.portfolio.save()
                        self.selected_portfolio = self.portfolio_name

                    except IntegrityError:
                        pass
                else:
                    pass

            elif self.portfolio and self.btn1_pressed == 'delete_portfolio':
                self.portfolio.delete()
                self.selected_portfolio = ''
                self.get_stock = 'empty'

            elif self.portfolio and self.btn1_pressed == 'add_new_symbol':
                try:
                    StockSelection.objects.create(
                        stock=Stock.objects.get(symbol=self.symbol),
                        quantity=0,
                        portfolio=self.portfolio)
                    self.symbol = ''
                    self.get_stock = 'yes'

                except (Stock.DoesNotExist, IntegrityError):
                    self.get_stock = 'no'

            else:
                assert False, f'check value btn1_pressed: {self.btn1_pressed}'

        else:
            pass

    def change_quantity_or_delete_symbol(self):

        if self.btn2_pressed:
            try:
                symbol, quantity = self.btn2_pressed.split(',')
                symbol = symbol.strip()
                quantity = quantity.strip()

            except ValueError:
                self.get_stock = 'no'
                return

            print(f'button two: {self.btn2_pressed, symbol, quantity}')

            if self.portfolio and quantity != 'delete':
                stock = self.portfolio.stocks.get(stock__symbol=symbol)
                stock.quantity = quantity
                stock.save()
                self.get_stock = 'yes'

            elif self.portfolio and quantity == 'delete':
                self.portfolio.stocks.get(stock__symbol=symbol).delete()
                self.get_stock = 'yes'

            else:
                assert False, f'check value of btn2_pressed: {self.btn2_pressed}'

        else:
            pass

    def get_stock_info(self):

        if self.portfolio:
            if self.get_stock == 'yes':
                print('get stock')
                self.stocks = self.wtd.get_portfolio_stock_info(self.portfolio)

            elif self.get_stock == 'no':
                self.stocks = json.loads(self.request.session.get('stock_info'))

            elif self.get_stock == 'empty':
                self.stocks = []

            else:
                assert False, f'invalid selection for get_stock: {self.get_stock}'

        else:
            self.stocks = []
