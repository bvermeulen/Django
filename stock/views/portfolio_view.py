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


@method_decorator(login_required, name='dispatch')
class PortfolioView(View):

    form_class = PortfolioForm
    template_name = 'finance/portfolio.html'

    def get(self, request):
        selected_portfolio = request.session.get('selected_portfolio', 'AEX')
        symbol = ''
        currency = request.session.get('currency', 'EUR')

        selected_portfolio = 'Techno'   # DEBUG
        symbol = 'AAPL'  # DEBUG

        form = self.form_class(
            user=request.user,
            initial={'selected_portfolio': selected_portfolio,
                     'symbol': symbol,
                     'currency': currency})


        print(form.fields['stocks'])

        context = {'form': form, }
        return render(request, self.template_name, context)
