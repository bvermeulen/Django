from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.quotes import QuoteView, IntraDayView, HistoryView
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
        ''' 5 <input> tags to be found:
            csrf token
            quote_string
            selected_portfolio
            markets (AEX, NYSE)
            Quote submit
        '''
        response = self.client.get(reverse('stock_quotes'))
        self.assertContains(response, '<input', 6)

    def test_valid_quote_string_returns_stock_info(self):
        data = {'markets': ['AEX'],
                'quote_string': 'wolters'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertEqual('WKL.AS', response.context['stock_info'][0]['symbol'])

    def test_valid_quote_string_has_a_to_intraday_view(self):
        data = {'markets': ['AEX'],
                'quote_string': 'kluwer'}
        url = reverse('stock_quotes')
        response = self.client.post(url, data)
        self.assertContains(response, 'href="/finance/stock_intraday/WKL.AS/"')

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

        file_name = 'stock/tests/quotes.html'
        with open(file_name, 'wt') as f:
            f.write(response.content.decode())


class IntraDayTests(QuotesTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_intraday', kwargs={'symbol':'AAPL'})
        self.response = self.client.get(self.url)

    def test_intraday_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_intraday_view_incorrect_symbol_redirects(self):
        response = self.client.get(reverse('stock_intraday',
                                           kwargs={'symbol':'Goobliecook'}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_intraday_url_resolves_IntraDayView(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, IntraDayView)

    def test_intraday_view_contains_link_to_home(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_intraday_view_contains_link_to_quotes(self):
        quotes_url = reverse('stock_quotes')
        self.assertContains(self.response, f'href="{quotes_url}"')

    def test_intraday_view_contains_link_to_history_1(self):
        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '1'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_3(self):
        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '3'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_5(self):
        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '5'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_max(self):
        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': 'max'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_response_contains_ref_to_worldtradingdata(self):
        self.assertEqual('www.worldtradingdata.com',
                         self.response.context['data_provider_url'])

        file_name = 'stock/tests/intraday.html'
        with open(file_name, 'wt') as f:
            f.write(self.response.content.decode())


class HistoryTests(QuotesTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '1'})
        self.response = self.client.get(self.url)

    def test_history_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '3'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '5'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': 'max'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

    def test_history_view_incorrect_symbol_redirects(self):
        history_url = reverse('stock_history',
                              kwargs={'symbol': 'GooblieDoog', 'period': '1'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_history_view_incorrect_period_redirects(self):
        history_url = reverse('stock_history', kwargs={'symbol': 'AAPL', 'period': '2'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_intraday_url_resolves_HistoryView(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, HistoryView)

    def test_history_view_contains_link_to_home(self):
        url = reverse('home')
        self.assertContains(self.response, f'href="{url}"')

    def test_history_view_contains_link_to_quotes(self):
        url = reverse('stock_quotes')
        self.assertContains(self.response, f'href="{url}"')

    def test_history_view_contains_link_to_intraday(self):
        symbol = self.response.context['stock_symbol']
        url = reverse('stock_intraday', kwargs={'symbol': symbol})
        self.assertContains(self.response, f'href="{url}"')

    def test_response_contains_ref_to_worldtradingdata(self):
        self.assertEqual('www.worldtradingdata.com',
                         self.response.context['data_provider_url'])

        file_name = 'stock/tests/history.html'
        with open(file_name, 'wt') as f:
            f.write(self.response.content.decode())
