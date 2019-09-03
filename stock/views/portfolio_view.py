from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.utils.decorators import method_decorator
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

    def get(self, request):
        symbol = ''
        currency = request.session.get('currency', 'EUR')

        symbol = 'AAPL'  # DEBUG

        form = self.form_class(
            user=request.user,
            initial={'symbol': symbol,
                     'currency': currency})

        context = {'form': form, }
        return render(request, self.template_name, context)

    def post(self, request):

        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            form_data = form.cleaned_data
            selected_portfolio = form_data.get('portfolios')

            stocks = Portfolio.objects.get(
                user=request.user,
                portfolio_name=selected_portfolio).stocks.all().order_by('stock__company')

            form = self.form_class(
                user=request.user,
                initial={'portfolio_name': selected_portfolio,
                         'portfolios': selected_portfolio,
                         'symbol': '',
                         'currency': 'EUR'})

        else:
            form = self.form_class(
                user=request.user,
                initial={'portfolio_name': '',
                         'portfolios': selected_portfolio,
                         'symbol': '',
                         'currency': 'EUR'})
            stocks = []

        context = {'form': form,
                   'stocks': stocks}
        return render(request, self.template_name, context)
