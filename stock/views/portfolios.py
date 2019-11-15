import json
from enum import Enum
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import format_decimal_number, format_amount_stocks
from stock.forms import PortfolioForm
from stock.models import Stock, Portfolio, StockSelection
from stock.module_stock import WorldTradingData

logger = Logger.getlogger()
d = Decimal
source = 'portfolio'


class GetStock(Enum):
    NO = 0
    YES = 1
    EMPTY = 3


@method_decorator(login_required, name='dispatch')
class PortfolioView(View):

    form_class = PortfolioForm
    template_name = 'finance/stock_portfolio.html'
    wtd = WorldTradingData()
    wtd.setup()

    def get(self, request):
        currency = request.session.get('currency', 'EUR')
        portfolios = request.session.get('selected_portfolio', '')
        user = request.user

        portfolio_name = ''
        stocks_value = '0'
        stocks = []

        if portfolios:
            try:
                self.portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=portfolios)
                portfolio_name = self.portfolio.portfolio_name
                stocks = self.get_stock_info(GetStock.YES, currency)
                stocks_value = self.wtd.calculate_stocks_value(stocks, currency)

                request.session['stock_info'] = json.dumps(stocks, cls=DjangoJSONEncoder)

            except Portfolio.DoesNotExist:
                portfolios = ''

        else:
            pass

        form = self.form_class(
            user=request.user,
            initial={'symbol': '',
                     'portfolio_name': portfolio_name,
                     'portfolios': portfolios,
                     'currencies': currency
                    })

        stocks_value = format_decimal_number(stocks_value)
        stocks = format_amount_stocks(stocks)
        context = {'form': form,
                   'stocks': stocks,
                   'stocks_value': stocks_value,
                   'source': source,
                  }

        return render(request, self.template_name, context)

    def post(self, request):
        # TODO add refresh button

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
            self.symbol = form_data.get('symbol').upper()
            self.btn1_pressed = form_data.get('btn1_pressed')
            self.btn2_pressed = form_data.get('btn2_pressed')
            self.previous_selected = request.session.get('selected_portfolio')
            previous_currency = request.session.get('currency')

            if (self.previous_selected != self.selected_portfolio or
                    previous_currency != currency):
                get_stock = GetStock.YES

            else:
                get_stock = GetStock.NO

            try:
                self.portfolio = Portfolio.objects.get(
                    user=self.user, portfolio_name=self.selected_portfolio)

            except Portfolio.DoesNotExist:
                self.portfolio = None
                self.selected_portfolio = ''
                self.btn1_pressed = ''
                self.btn2_pressed = ''
                get_stock = GetStock.EMPTY

            if self.new_portfolio:
                get_stock = self.create_new_portfolio()

            elif self.btn1_pressed:
                get_stock = self.rename_or_delete_portfolio_or_add_stock()

            elif self.btn2_pressed:
                get_stock = self.change_quantity_or_delete_symbol()

            else:
                pass

            # set portfolio name except if the portfolio has been deleted or
            # does not exist
            try:
                self.portfolio_name = self.portfolio.portfolio_name

            except AttributeError:
                self.portfolio_name = ''

            stocks = self.get_stock_info(get_stock, currency)
            stocks_value = self.wtd.calculate_stocks_value(stocks, currency)
            request.session['stock_info'] = json.dumps(stocks, cls=DjangoJSONEncoder)
            request.session['selected_portfolio'] = self.selected_portfolio
            request.session['currency'] = currency

            form = self.form_class(
                user=self.user,
                initial={'portfolio_name': self.portfolio_name,
                         'portfolios': self.selected_portfolio,
                         'symbol': self.symbol,
                         'currencies': currency})

            logger.info(f'user {self.user} [ip: {get_client_ip(self.request)}] '
                        f'views {self.selected_portfolio}')

        else:
            form = self.form_class(
                user=self.user,
                initial={'portfolios': '',
                         'portfolio_name': '',
                         'symbol': '',
                         'currencies': currency})

            stocks_value = '0'
            stocks = []

        stocks_value = format_decimal_number(stocks_value)
        stocks = format_amount_stocks(stocks)
        context = {'form': form,
                   'stocks': stocks,
                   'stocks_value': stocks_value,
                   'source': source,}

        return render(self.request, self.template_name, context)

    def create_new_portfolio(self):
        try:
            self.portfolio = Portfolio.objects.create(
                user=self.user, portfolio_name=self.new_portfolio)
            self.selected_portfolio = self.new_portfolio
            get_stock = GetStock.EMPTY

        except IntegrityError:
            # patch in case initial choice portfolios is None then for some reason
            # choicefield will return the first option. In that case reset all
            if not self.previous_selected:
                self.portfolio = None
                self.selected_portfolio = self.previous_selected
                get_stock = GetStock.EMPTY

            else:
                self.new_portfolio = ''
                get_stock = GetStock.NO

        return get_stock

    def rename_or_delete_portfolio_or_add_stock(self):
        ''' actions when btn1 is pressed '''
        logger.warning(f'{self.portfolio}: check existance of portfolio')

        if not self.portfolio_name:
            return GetStock.NO

        if self.btn1_pressed == 'rename_portfolio':
            get_stock = GetStock.NO
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
            self.portfolio = None
            self.selected_portfolio = ''
            self.portfolio_name = ''
            get_stock = GetStock.EMPTY

        elif self.btn1_pressed == 'add_new_symbol':
            try:
                StockSelection.objects.create(
                    stock=Stock.objects.get(symbol=self.symbol),
                    quantity=0,
                    portfolio=self.portfolio)
                self.symbol = ''
                get_stock = GetStock.YES

            except (Stock.DoesNotExist, IntegrityError):
                get_stock = GetStock.NO

        else:
            logger.warning(f'Invalid value btn1_pressed: {self.btn1_pressed}')

        return get_stock

    def change_quantity_or_delete_symbol(self):
        ''' actions when btn 2 is pressed '''
        logger.warning(f'{self.portfolio}: check existance of portfolio')

        try:
            symbol, quantity = self.btn2_pressed.split(',')
            symbol = symbol.strip()
            quantity = quantity.strip()

        except ValueError:
            return GetStock.NO

        if quantity != 'delete':
            stock = self.portfolio.stocks.get(stock__symbol=symbol)
            stock.quantity = quantity
            stock.save()
            get_stock = GetStock.YES

        elif quantity == 'delete':
            self.portfolio.stocks.get(stock__symbol=symbol).delete()
            get_stock = GetStock.YES

        else:
            logger.warning(f'Invalid value of btn2_pressed: {self.btn2_pressed}')

        return get_stock

    def get_stock_info(self, get_stock, currency):
        ''' get stock info depending of get_stock status'''
        stocks = []
        if self.portfolio:

            if get_stock == GetStock.YES:
                stocks = self.wtd.get_portfolio_stock_info(self.portfolio, currency)

            elif get_stock == GetStock.NO:
                try:
                    stocks = json.loads(self.request.session.get('stock_info'))

                except TypeError:
                    stocks = self.wtd.get_portfolio_stock_info(self.portfolio, currency)

            elif get_stock == GetStock.EMPTY:
                # stocks is empty list already fullfilled
                pass

            else:
                logger.warning(f'invalid selection for get_stock: {get_stock}')

        else:
            # stocks is empty list already fullfilled
            pass

        return stocks
