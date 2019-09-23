import json
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from stock.forms import PortfolioForm
from stock.models import Stock, Portfolio, StockSelection
from stock.module_stock import WorldTradingData, start_currency_update

logger = Logger.getlogger()
d = Decimal
# start_currency_update()

@method_decorator(login_required, name='dispatch')
class PortfolioView(View):

    form_class = PortfolioForm
    template_name = 'finance/stock_portfolio.html'
    wtd = WorldTradingData()

    def get(self, request):
        currency = request.session.get('currency', 'EUR')
        request.session['selected_portfolio'] = None

        form = self.form_class(
            user=request.user,
            initial={'symbol': None,
                     'portfolios': None,
                     'currencies': currency})

        stocks_value = d(0)
        context = {'form': form,
                   'stocks': [],
                   'stocks_value': f'{stocks_value:,.2f}',
                  }

        return render(request, self.template_name, context)

    def post(self, request):
        self.request = request
        self.user = self.request.user
        currency = request.session.get('currency', 'EUR')

        form = self.form_class(self.request.POST, user=self.user)
        if form.is_valid():
            form_data = form.cleaned_data
            currency = form_data.get('currencies')
            self.selected_portfolio = form_data.get('portfolios')
            self.portfolio_name = form_data.get('portfolio_name')
            self.new_portfolio = form_data.get('new_portfolio')
            self.symbol = form_data.get('symbol')
            self.btn1_pressed = form_data.get('btn1_pressed')
            self.btn2_pressed = form_data.get('btn2_pressed')
            self.previous_selected = request.session.get('selected_portfolio')

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

            if self.new_portfolio != '':
                self.create_new_portfolio()

            if self.portfolio:
                if self.btn1_pressed:
                    self.rename_or_delete_portfolio_or_add_stock()

                elif self.btn2_pressed:
                    self.change_quantity_or_delete_symbol()

            self.get_stock_info(self.get_stock)
            stocks_value = self.wtd.calculate_stocks_value(self.stocks, currency)
            request.session['stock_info'] = json.dumps(self.stocks, cls=DjangoJSONEncoder)
            request.session['selected_portfolio'] = self.selected_portfolio
            request.session['currency'] = currency

            form = self.form_class(
                user=self.user,
                initial={'portfolio_name': self.selected_portfolio,
                         'portfolios': self.selected_portfolio,
                         'symbol': self.symbol,
                         'currencies': currency})

            logger.info(f'user {self.user} [ip: {get_client_ip(self.request)}] '
                        f'views {self.selected_portfolio}')
        else:
            form = self.form_class(
                user=self.user,
                initial={'portfolio_name': '',
                         'symbol': '',
                         'currencies': currency})

            stocks_value = d(0)
            self.stocks = []

        context = {'form': form,
                   'stocks': self.stocks,
                   'stocks_value': f'{stocks_value:,.2f}'}

        return render(self.request, self.template_name, context)

    def create_new_portfolio(self):

        if self.new_portfolio != '':
            try:
                self.portfolio = Portfolio.objects.create(
                    user=self.user, portfolio_name=self.new_portfolio)
                self.selected_portfolio = self.new_portfolio
                self.get_stock = 'empty'

            except IntegrityError:
                pass

    def rename_or_delete_portfolio_or_add_stock(self):
        ''' actions when btn1 is pressed '''
        assert self.portfolio, "check existance of portfolio"

        if self.btn1_pressed == 'rename_portfolio':
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

        elif self.btn1_pressed == 'delete_portfolio':
            self.portfolio.delete()
            self.selected_portfolio = ''
            self.get_stock = 'empty'

        elif self.btn1_pressed == 'add_new_symbol':
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

    def change_quantity_or_delete_symbol(self):
        ''' actions when btn 2 is pressed '''
        assert self.portfolio, "check existance of portfolio"

        try:
            symbol, quantity = self.btn2_pressed.split(',')
            symbol = symbol.strip()
            quantity = quantity.strip()

        except ValueError:
            self.get_stock = 'no'
            return

        if quantity != 'delete':
            stock = self.portfolio.stocks.get(stock__symbol=symbol)
            stock.quantity = quantity
            stock.save()
            self.get_stock = 'yes'

        elif quantity == 'delete':
            self.portfolio.stocks.get(stock__symbol=symbol).delete()
            self.get_stock = 'yes'

        else:
            assert False, f'check value of btn2_pressed: {self.btn2_pressed}'

    def get_stock_info(self, get_stock):
        ''' get stock info depending of get_stock status'''
        self.stocks = []
        if self.portfolio:

            if get_stock == 'yes':
                self.stocks = self.wtd.get_portfolio_stock_info(self.portfolio)

            elif get_stock == 'no':
                try:
                    self.stocks = json.loads(self.request.session.get('stock_info'))

                except TypeError:
                    self.stocks = self.wtd.get_portfolio_stock_info(self.portfolio)

            elif get_stock == 'empty':
                pass

            else:
                assert False, f'invalid selection for get_stock: {get_stock}'

        else:
            pass
