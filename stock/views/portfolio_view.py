from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from stock.forms import PortfolioForm
from stock.models import Exchange, Stock, Portfolio
from stock.module_stock import WorldTradingData
from howdimain.utils.plogger import Logger

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

            # TODO check input names for portfolio name, symbol and new_portfolio

            try:
                portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=selected_portfolio)

            except Portfolio.DoesNotExist:
                portfolio = None

            # create new portfolio
            if new_portfolio != '':
                try:
                    Portfolio.objects.create(user=user, portfolio_name=new_portfolio)
                except IntegrityError:
                    print('cannot create portfolio')

            if (portfolio and btn1_pressed == 'rename_portfolio'
                    and portfolio_name != selected_portfolio):
                portfolio.portfolio_name = portfolio_name
                portfolio.save()
                selected_portfolio = portfolio_name

            if portfolio and btn_delete_portfolio == 'delete_portfolio':
                portfolio.delete()


            if portfolio:
                stocks = self.wtd.get_portfolio_stock_info(user, portfolio)

            else:
                stocks = []

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
