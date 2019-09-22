from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.portfolios import PortfolioView
from ..models import Currency, Exchange, Stock, StockSelection, Portfolio

class PortfolioTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.test_user = 'test_user'
        cls.test_user_pw = '123'
        default_user = 'default_user'

        test_user = User.objects.create_user(username=cls.test_user,
                                             email='test@howdiweb.nl',
                                             password=cls.test_user_pw)

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



class TestPortfolioView(PortfolioTestCase):

    def setUp(self):
        self.client.login(username=self.test_user, password=self.test_user_pw)

    def test_portfolio_view_status_code(self):
        response = self.client.get(reverse('portfolio'))
        self.assertEqual(response.status_code, 200)

    def test_url_resolves_PortfolioView(self):
        view = resolve('/finance/portfolio/')
        self.assertEqual(view.func.view_class, PortfolioView)

    def test_view_contains_link_to_home(self):
        response = self.client.get(reverse('portfolio'))
        home_url = reverse('home')
        self.assertContains(response, f'href="{home_url}"')

    def test_view_contains_link_to_quotes(self):
        response = self.client.get(reverse('portfolio'))
        quotes_url = reverse('stock_quotes')
        self.assertContains(response, f'href="{quotes_url}"')

    def test_response_contains_csrf_token(self):
        response = self.client.get(reverse('portfolio'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_not_logged_in_redirects_to_login_page(self):
        self.client.logout()
        response = self.client.post(reverse('portfolio'))
        login_url = reverse('login') + f'?next={reverse("portfolio")}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

class TestPortfolioPost(PortfolioTestCase):

    def setUp(self):
        self.client.login(username=self.test_user, password=self.test_user_pw)

    def test_correct_number_input_tags(self):
        ''' 4 <input> tags to be found:
            csrf token
            new_portfolio
            portfolio_name
            symbol
        '''
        response = self.client.get(reverse('portfolio'))
        self.assertContains(response, '<input', 4)

    def test_select_portfolio(self):
        data = {'currencies': 'EUR',
                'portfolios': 'test_portfolio'}
        response = self.client.post(reverse('portfolio'), data)
        self.assertEqual('AAPL', response.context['stocks'][0]['symbol'])

    def test_create_html(self):
        data = {'currencies': 'EUR',
                'portfolios': 'test_portfolio'}
        response = self.client.post(reverse('portfolio'), data)

        file_name = 'stock/tests/test_portfolio.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(response.content.decode())
