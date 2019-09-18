from pprint import pprint
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.quotes import QuoteView
from ..models import Currency, Exchange, Stock, StockSelection, Portfolio


class QuestesTests(TestCase):
    def setUp(self):
        self.test_user = 'test'
        self.test_user_pw = '123'
        self.default_user = 'default_user'

        self.test_user = User.objects.create_user(username=self.test_user,
                                                  email='test@howdiweb.nl',
                                                  password=self.test_user_pw)

        self.default_user = User.objects.create_user(username='default_user',
                                                     email='default@howdiweb.nl',
                                                     password='456')

        self.usd = Currency.objects.create(currency='USD',
                                           usd_exchange_rate='1.0')

        self.eur = Currency.objects.create(currency='EUR',
                                           usd_exchange_rate='0.9')

        self.nyse = Exchange.objects.create(exchange_short='NYSE',
                                            exchange_long='New York Stock Exchange',
                                            time_zone_name='CET',)

        self.aex = Exchange.objects.create(exchange_short='AEX',
                                           exchange_long='Amsterdam AEX',
                                           time_zone_name='ECT',)

        self.apple = Stock.objects.create(symbol='AAPL',
                                          company='Apple',
                                          currency=self.usd,
                                          exchange=self.nyse,)

        self.rds = Stock.objects.create(symbol='RDSA.AS',
                                        company='Royal Dutch Shell',
                                        currency=self.eur,
                                        exchange=self.aex)

        self.john_portfolio = Portfolio.objects.create(portfolio_name='test_portfolio',
                                                       user=self.test_user)

        StockSelection.objects.create(stock=self.apple,
                                      quantity=10,
                                      portfolio=self.john_portfolio)

        self.default_aex = Portfolio.objects.create(portfolio_name='AEX',
                                                    user=self.default_user,)

        StockSelection.objects.create(stock=self.rds,
                                      quantity=1,
                                      portfolio=self.default_aex)

    def test_output_html(self):
        file_name = 'stock/tests/quotes.html'
        response = self.client.get(reverse('stock_quotes'))
        with open(file_name, 'wt') as f:
            f.write(response.content.decode())

    def test_quotes_view_status_code(self):
        response = self.client.get(reverse('stock_quotes'))
        self.assertEqual(response.status_code, 200)

    def test_quotes_url_resolves_QuoteView(self):
        view = resolve('/finance/stock_quote/')
        self.assertEqual(view.func.view_class, QuoteView)

    def test_quote_view_contains_link_to_home(self):
        response = self.client.get(reverse('stock_quotes'))
        home_url = reverse('home')
        self.assertContains(response, f'href="{home_url}"')

    def test_response_contains_csrf_token(self):
        response = self.client.get(reverse('stock_quotes'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_correct_number_input_tags(self):
        ''' 5 <input> tags to be found:
            csrf token
            quote_string
            markets (AEX, NYSE)
            Quote submit
        '''
        response = self.client.get(reverse('stock_quotes'))
        self.assertContains(response, '<input', 5)

    def test_valid_quote_string_returns_stock_info(self):
        data = {'quote_string': 'Apple'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual('AAPL', response.context['stock_info'][0]['symbol'])

    def test_valid_quote_string_has_a_to_intraday_view(self):
        data = {'quote_string': 'Apple'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        pprint(response.content)

    def test_(self):
        print('hallo')