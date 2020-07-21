from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from howdimain.howdimain_vars import URL_ALPHAVANTAGE, URL_WORLDTRADE, URL_FMP
from ..views.portfolios import PortfolioView
from ..models import Currency, Exchange, Stock, StockSelection, Portfolio

URL_PROVIDER = URL_FMP
d = Decimal


class PortfolioTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.test_user_name = 'test_user'
        cls.test_user_pw = '123'
        default_user = 'default_user'

        cls.test_user = User.objects.create_user(username=cls.test_user_name,
                                                 email='test@howdiweb.nl',
                                                 password=cls.test_user_pw)

        default_user = User.objects.create_user(username='default_user',
                                                email='default@howdiweb.nl',
                                                password='456')

        usd = Currency.objects.create(currency='USD',
                                      usd_exchange_rate='1.0')

        cls.eur = Currency.objects.create(currency='EUR',
                                          usd_exchange_rate='0.9')

        nyse = Exchange.objects.create(exchange_short='NYSE',
                                       exchange_long='New York Stock Exchange',
                                       time_zone_name='America/New_York',)

        aex = Exchange.objects.create(exchange_short='AEX',
                                      exchange_long='Amsterdam AEX',
                                      time_zone_name='Europe/Amsterdam',)

        cls.apple = Stock.objects.create(symbol='AAPL',
                                         company='Apple',
                                         currency=usd,
                                         exchange=nyse,)

        cls.rds = Stock.objects.create(symbol='RDSA.AS',
                                       company='Royal Dutch Shell',
                                       currency=cls.eur,
                                       exchange=aex)

        Stock.objects.create(symbol='WKL.AS',
                             company='Wolters Kluwer',
                             currency=cls.eur,
                             exchange=aex)

        cls.test_portfolio = Portfolio.objects.create(portfolio_name='test_portfolio',
                                                      user=cls.test_user)

        StockSelection.objects.create(stock=cls.apple,
                                      quantity=10,
                                      portfolio=cls.test_portfolio)

        default_aex = Portfolio.objects.create(portfolio_name='AEX_index',
                                               user=default_user,)

        StockSelection.objects.create(stock=cls.rds,
                                      quantity=1,
                                      portfolio=default_aex)


class TestPortfolioView(PortfolioTestCase):

    def setUp(self):
        self.client.login(username=self.test_user_name, password=self.test_user_pw)

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
        response = self.client.get(reverse('portfolio'))
        login_url = reverse('login') + f'?next={reverse("portfolio")}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

    def test_response_contains_ref_to_url_provider(self):
        response = self.client.get(reverse('portfolio'))
        self.assertEqual(URL_PROVIDER, response.context['data_provider_url'])


class TestPortfolioPost(PortfolioTestCase):

    def setUp(self):
        self.client.login(username=self.test_user_name, password=self.test_user_pw)
        self.data = {'currencies': 'EUR'}

    def test_correct_number_input_tags(self):
        ''' 4 <input> tags to be found:
            csrf token
            new_portfolio
            portfolio_name
            symbol
        '''
        session = self.client.session
        session['selected_portfolio'] = 'test_portfolio'
        session.save()
        response = self.client.get(reverse('portfolio'))
        self.assertContains(response, '<input', 4)

    def test_correct_number_input_tags_non_exisistent_portfolio(self):
        ''' 4 <input> tags to be found:
            csrf token
            new_portfolio
            portfolio_name
            symbol
        '''
        session = self.client.session
        session['selected_portfolio'] = 'i_do_not_exist'
        session.save()
        response = self.client.get(reverse('portfolio'))
        self.assertContains(response, '<input', 4)

    def test_select_portfolio(self):
        self.data['portfolios'] = 'test_portfolio'
        response = self.client.post(reverse('portfolio'), self.data)
        self.assertEqual('AAPL', response.context['stocks'][0]['symbol'])

    def test_new_portfolio(self):
        self.data['new_portfolio'] = 'my_new_portfolio'
        self.client.post(reverse('portfolio'), self.data)
        self.assertEqual(2, len(Portfolio.objects.filter(user=self.test_user)))

    def test_delete_portfolio(self):
        Portfolio.objects.create(user=self.test_user,
                                 portfolio_name='my_new_portfolio')
        self.data['btn1_pressed'] = 'delete_portfolio'
        self.data['portfolios'] = 'my_new_portfolio'
        self.data['portfolio_name'] = 'my_new_portfolio'
        self.client.post(reverse('portfolio'), self.data)
        self.assertEqual(1, len(Portfolio.objects.filter(user=self.test_user)))

    def test_rename_portfolio(self):
        Portfolio.objects.create(user=self.test_user,
                                 portfolio_name='my_new_portfolio')
        self.data['btn1_pressed'] = 'rename_portfolio'
        self.data['portfolios'] = 'my_new_portfolio'
        self.data['portfolio_name'] = 'HAHA MAIN'
        response = self.client.post(reverse('portfolio'), self.data)
        self.assertEqual(1, len(Portfolio.objects.filter(user=self.test_user,
                                                         portfolio_name='HAHA MAIN')))
        self.assertEqual('HAHA MAIN', response.context['form']['portfolio_name'].value())
        self.assertEqual('HAHA MAIN', response.context['form']['portfolios'].value())

    def test_add_symbol(self):
        self.data['portfolios'] = 'test_portfolio'
        self.data['portfolio_name'] = 'test_portfolio'
        self.data['btn1_pressed'] = 'add_new_symbol'
        self.data['symbol'] = 'RDSA.AS'
        response = self.client.post(reverse('portfolio'), self.data)
        stocks_portfolio_db = Portfolio.objects.filter(
            user=self.test_user, portfolio_name='test_portfolio').first().stocks.all()
        self.assertEqual(2, len(stocks_portfolio_db))
        self.assertEqual('RDSA.AS', stocks_portfolio_db[1].stock.symbol)
        self.assertEqual('RDSA.AS', response.context['stocks'][1]['symbol'])

    def test_link_to_intraday_view(self):
        self.data['portfolios'] = 'test_portfolio'
        self.data['portfolio_name'] = 'test_portfolio'
        response = self.client.post(reverse('portfolio'), self.data)
        self.assertContains(response, 'href="/finance/stock_intraday/portfolio/AAPL/"')

    def test_add_invalid_symbol(self):
        self.data['portfolios'] = 'test_portfolio'
        self.data['btn1_pressed'] = 'add_new_symbol'
        self.data['symbol'] = 'HAHAHA'
        stocks_portfolio_db = Portfolio.objects.filter(
            user=self.test_user, portfolio_name='test_portfolio').first().stocks.all()
        self.assertEqual(1, len(stocks_portfolio_db))
        self.assertEqual('AAPL', stocks_portfolio_db[0].stock.symbol)
        response = self.client.post(reverse('portfolio'), self.data)
        self.assertEqual(1, len(response.context['stocks']))

    def test_change_quantity(self):
        self.data['portfolios'] = 'test_portfolio'
        self.data['change_qty_btn_pressed'] = 'AAPL, 5'
        response = self.client.post(reverse('portfolio'), self.data)
        aapl = StockSelection.objects.filter(stock=self.apple,
                                             portfolio=self.test_portfolio)
        self.assertEqual('5', aapl.first().quantity)
        self.assertEqual('5', response.context['stocks'][0]['quantity'])

    def test_delete_stock(self):
        # first add a new symbol to the portfolio
        StockSelection.objects.create(
            stock=self.rds, quantity=0, portfolio=self.test_portfolio)

        self.data['portfolios'] = 'test_portfolio'
        self.data['delete_symbol_btn_pressed'] = 'RDSA.AS'
        response = self.client.post(reverse('portfolio'), self.data)
        stocks_portfolio_db = Portfolio.objects.filter(
            user=self.test_user, portfolio_name='test_portfolio').first().stocks.all()
        self.assertEqual(1, len(stocks_portfolio_db))
        self.assertEqual('AAPL', stocks_portfolio_db[0].stock.symbol)
        self.assertEqual('AAPL', response.context['stocks'][0]['symbol'])

    def test_portfolio_euro_value(self):
        self.data['portfolios'] = 'test_portfolio'
        response = self.client.post(reverse('portfolio'), self.data)

        stocks_value = d(response.context['totals']['value'].replace(',', ''))

        value_eur = 0
        for stock in response.context['stocks']:
            value_eur += d(stock['value'].replace(',', ''))

        self.assertEqual(stocks_value.quantize(d('0.01')), value_eur.quantize(d('0.01')))

    def test_portfolio_usd_value(self):
        self.data['portfolios'] = 'test_portfolio'
        self.data['currencies'] = 'USD'
        response = self.client.post(reverse('portfolio'), self.data)

        stocks_value = d(response.context['totals']['value'].replace(',', ''))

        value_usd = 0
        for stock in response.context['stocks']:
            value_usd += d(stock['quantity']) * d(stock['price'].replace(',', ''))

        if value_usd > 1000:
            value_usd = d(f'{value_usd:.0f}')

        else:
            value_usd = d(f'{value_usd:.2f}')

        self.assertEqual(stocks_value.quantize(d('0.01')), value_usd.quantize(d('0.01')))

    def test_portfolio_value_change(self):
        self.data['portfolios'] = 'test_portfolio'
        response = self.client.post(reverse('portfolio'), self.data)

        stocks_value = d(response.context['totals']['value_change'].replace(',', ''))

        value = 0
        for stock in response.context['stocks']:
            value += d(stock['value_change'].replace(',', ''))

        self.assertEqual(stocks_value.quantize(d('0.01')), value.quantize(d('0.01')))

    def test_create_html(self):
        self.client.get(reverse('portfolio'))
        self.data['portfolios'] = 'test_portfolio'
        response = self.client.post(reverse('portfolio'), self.data)

        file_name = 'stock/tests/test_portfolio.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(response.content.decode())
