import json
from enum import Enum
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from howdimain.howdimain_vars import BASE_CURRENCIES, STOCK_DETAILS
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import (
    add_display_tokens, format_totals_values, format_and_sort_stocks)
from stock.models import Person, Stock, Portfolio, StockSelection
from stock.forms import PortfolioForm
from stock.module_stock import TradingData

logger = Logger.getlogger()
d = Decimal
source = 'portfolio'


class GetStock(Enum):
    NO = 0
    YES = 1
    EMPTY = 3


@method_decorator(login_required, name='dispatch')
class PortfolioView(View):

    portfolio_form = PortfolioForm
    template_name = 'finance/stock_portfolio.html'
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request):
        currency = request.session.get('currency', BASE_CURRENCIES[0][0])
        stockdetail = request.session.get('stockdetail', STOCK_DETAILS[0][0])
        selected_portfolio = request.session.get('selected_portfolio', '')
        user = request.user
        # add Person class to user
        if user.is_authenticated:
            user.__class__ = Person

        portfolio_name = ''
        stocks = []

        if selected_portfolio:
            try:
                self.portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=selected_portfolio)
                portfolio_name = self.portfolio.portfolio_name
                stocks = self.get_stock_info(GetStock.YES, currency)
                request.session['stock_info'] = json.dumps(stocks, cls=DjangoJSONEncoder)

            except Portfolio.DoesNotExist:
                selected_portfolio = ''

        else:
            pass

        form = self.portfolio_form(
            user=user,
            initial={'symbol': '',
                     'portfolio_name': portfolio_name,
                     'portfolios': selected_portfolio,
                     'currencies': currency,
                     'stockdetails': stockdetail,
                     'exchangerate': self.td.get_usd_euro_exchangerate(currency),
                    })

        totals_values = format_totals_values(*self.td.calculate_stocks_value(stocks))
        stocks = add_display_tokens(stocks)
        stocks = format_and_sort_stocks(stocks)
        context = {'form': form,
                   'stocks': stocks,
                   'totals': totals_values,
                   'source': source,
                   'data_provider_url': self.data_provider_url,
                  }
        return render(request, self.template_name, context)

    def post(self, request):
        # TODO add refresh button

        self.request = request
        self.user = self.request.user
        # add Person class to user
        if self.user.is_authenticated:
            self.user.__class__ = Person

        currency = request.session.get('currency', BASE_CURRENCIES[0][0])
        stockdetail = request.session.get('stockdetail', STOCK_DETAILS[0][0])

        form = self.portfolio_form(self.request.POST, user=self.user)
        if form.is_valid():
            form_data = form.cleaned_data
            currency = form_data.get('currencies')
            stockdetail = form_data.get('stockdetails')
            self.selected_portfolio = form_data.get('portfolios')
            self.portfolio_name = form_data.get('portfolio_name')
            self.new_portfolio = form_data.get('new_portfolio')
            self.symbol = form_data.get('symbol').upper()
            self.btn1_pressed = form_data.get('btn1_pressed')
            self.change_qty_btn_pressed = form_data.get('change_qty_btn_pressed')
            self.delete_symbol_btn_pressed = form_data.get('delete_symbol_btn_pressed')
            self.previous_selected = request.session.get('selected_portfolio')
            previous_currency = request.session.get('currency')

            if (self.previous_selected == self.selected_portfolio and
                    previous_currency == currency):
                get_stock = GetStock.NO

            else:
                get_stock = GetStock.YES

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

            elif self.change_qty_btn_pressed:
                get_stock = self.change_quantity_symbol()

            elif self.delete_symbol_btn_pressed:
                get_stock = self.delete_symbol()

            else:
                pass

            # set portfolio name except if the portfolio has been deleted or
            # does not exist
            try:
                self.portfolio_name = self.portfolio.portfolio_name

            except AttributeError:
                self.portfolio_name = ''

            stocks = self.get_stock_info(get_stock, currency)
            request.session['stock_info'] = json.dumps(stocks, cls=DjangoJSONEncoder)
            request.session['selected_portfolio'] = self.selected_portfolio
            request.session['currency'] = currency
            request.session['stockdetail'] = stockdetail

            form = self.portfolio_form(
                user=self.user,
                initial={'portfolio_name': self.portfolio_name,
                         'portfolios': self.selected_portfolio,
                         'symbol': self.symbol,
                         'currencies': currency,
                         'stockdetails': stockdetail,
                         'exchangerate': self.td.get_usd_euro_exchangerate(currency),
                        })

            logger.info(f'user {self.user} [ip: {get_client_ip(self.request)}] '
                        f'views {self.selected_portfolio}')

        else:
            form = self.portfolio_form(
                user=self.user,
                initial={'portfolios': '',
                         'portfolio_name': '',
                         'symbol': '',
                         'currencies': currency,
                         'stockdetails': stockdetail,
                         'exchangerate': self.td.get_usd_euro_exchangerate(currency),
                        })

            stocks = []

        totals_values = format_totals_values(*self.td.calculate_stocks_value(stocks))
        stocks = add_display_tokens(stocks)
        stocks = format_and_sort_stocks(stocks)
        context = {
            'form': form,
            'stocks': stocks,
            'totals': totals_values,
            'source': source,
            'data_provider_url': self.data_provider_url,
        }
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
        if not self.portfolio:
            logger.warning(f'{self.portfolio}: check existance of portfolio')
            return GetStock.NO

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
                    stock=Stock.objects.get(symbol_ric=self.symbol),
                    quantity=0,
                    portfolio=self.portfolio)

                self.symbol = ''
                get_stock = GetStock.YES

            except (Stock.DoesNotExist, IntegrityError, ValueError):
                get_stock = GetStock.NO

        else:
            logger.warning(f'Invalid value btn1_pressed: {self.btn1_pressed}')

        return get_stock

    def change_quantity_symbol(self):
        ''' change quantiy of symbol when change_quantity_btn is pressed '''
        if not self.portfolio:
            logger.warning(f'{self.portfolio}: check existance of portfolio')
            return GetStock.NO

        try:
            symbol, quantity = self.change_qty_btn_pressed.split(',')
            symbol = symbol.strip()
            quantity = quantity.strip()

        except ValueError:
            return GetStock.NO

        portfolio_selected_stock = self.portfolio.stocks.get(stock__symbol_ric=symbol)

        if  portfolio_selected_stock.stock.currency.currency != 'N/A':
            portfolio_selected_stock.quantity = quantity
            portfolio_selected_stock.save()
            get_stock = GetStock.YES

        else:
            get_stock = GetStock.NO

        return get_stock

    def delete_symbol(self):
        ''' delete symbol from portfolio when delete symbol btn is pressed '''
        if not self.portfolio:
            logger.warning(f'{self.portfolio}: check existance of portfolio')
            return GetStock.NO

        self.portfolio.stocks.get(
            stock__symbol_ric=self.delete_symbol_btn_pressed).delete()

        return GetStock.YES

    def get_stock_info(self, get_stock, currency):
        ''' get stock info depending of get_stock status'''
        stocks = []
        if self.portfolio:

            if get_stock == GetStock.YES:
                stocks = self.td.get_portfolio_stock_info(self.portfolio, currency)

            elif get_stock == GetStock.NO:
                try:
                    stocks = json.loads(self.request.session.get('stock_info'))

                except TypeError:
                    stocks = self.td.get_portfolio_stock_info(self.portfolio, currency)

            elif get_stock == GetStock.EMPTY:
                # stocks is empty list already fullfilled
                pass

            else:
                logger.warning(f'invalid selection for get_stock: {get_stock}')

        else:
            # stocks is empty list already fullfilled
            pass

        return stocks
