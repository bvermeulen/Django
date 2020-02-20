from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.quotes import QuoteView
from ..models import Currency, Exchange, Stock, StockSelection, Portfolio

class QuotesTestCase(TestCase):

    def setUp(self):
        self.test_user = 'test_user'
        self.test_user_pw = '123'
        default_user = 'default_user'

        test_user = User.objects.create_user(username=self.test_user,
                                             email='test@howdiweb.nl',
                                             password=self.test_user_pw)

        default_user = User.objects.create_user(username='default_user',
                                                email='default@howdiweb.nl',
                                                password='456')

        usd = Currency.objects.create(currency='USD',
                                      usd_exchange_rate='1.0')

        eur = Currency.objects.create(currency='EUR',
                                      usd_exchange_rate='0.9')

        nyse = Exchange.objects.create(exchange_short='NYSE',
                                       exchange_long='New York Stock Exchange',
                                       time_zone_name='CET',)

        aex = Exchange.objects.create(exchange_short='AEX',
                                      exchange_long='Amsterdam AEX',
                                      time_zone_name='ECT',)

        apple = Stock.objects.create(symbol='AAPL',
                                     company='Apple',
                                     currency=usd,
                                     exchange=nyse,)

        rds = Stock.objects.create(symbol='RDSA.AS',
                                   company='Royal Dutch Shell',
                                   currency=eur,
                                   exchange=aex)

        Stock.objects.create(symbol='WKL.AS',
                             company='Wolters Kluwer',
                             currency=eur,
                             exchange=aex)

        test_portfolio = Portfolio.objects.create(portfolio_name='test_portfolio',
                                                  user=test_user)

        StockSelection.objects.create(stock=apple,
                                      quantity=10,
                                      portfolio=test_portfolio)

        default_aex = Portfolio.objects.create(portfolio_name='AEX_index',
                                               user=default_user,)

        StockSelection.objects.create(stock=rds,
                                      quantity=1,
                                      portfolio=default_aex)


class QuotesViewTestCase(QuotesTestCase):

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
        ''' 6 <input> tags to be found:
            csrf token
            quote_string
            selected_portfolio
            markets AEX
            markets NYSE
        '''
        response = self.client.get(reverse('stock_quotes'))
        self.assertContains(response, '<input', 5)

    def test_not_logged_does_not_give_my_portfolio(self):
        response = self.client.get(reverse('stock_quotes'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'My Portfolio')

    def test_valid_quote_string_returns_stock_info(self):
        data = {'markets': ['AEX'],
                'quote_string': 'wolters'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual('WKL.AS', response.context['stock_info'][0]['symbol'])

    def test_valid_quote_string_has_a_link_to_intraday_view(self):
        data = {'markets': ['AEX'],
                'quote_string': 'kluwer'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertContains(response, 'href="/finance/stock_intraday/quotes/WKL.AS/"')

    def test_invalid_quote_string_returns_empty_stock_info(self):
        data = {'quote_string': 'Goobliecook'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual(True, not response.context['stock_info'])

    def test_select_portfolio_returns_stock_info(self):
        data = {'quote_string': 'Goobliecook',
                'selected_portfolio': 'AEX_index',
               }

        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual('RDSA.AS', response.context['stock_info'][0]['symbol'])

    def test_user_portfolio_returns_stock_info(self):
        self.client.login(username=self.test_user, password=self.test_user_pw)
        data = {'quote_string': 'Goobliecook',
                'selected_portfolio': 'test_portfolio',
               }

        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual('AAPL', response.context['stock_info'][0]['symbol'])

    def test_response_contains_ref_to_worldtradingdata(self):
        response = self.client.get(reverse('stock_quotes'))
        self.assertEqual('www.worldtradingdata.com',
                         response.context['data_provider_url'])

        file_name = 'stock/tests/test_quotes.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(response.content.decode())
