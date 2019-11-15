from django.urls import reverse, resolve
from django.test import TestCase
from ..views.plots import IntraDayView, HistoryView
from ..models import Currency, Exchange, Stock

class PlotsTestCase(TestCase):

    def setUp(self):
        usd = Currency.objects.create(currency='USD',
                                      usd_exchange_rate='1.0')

        nyse = Exchange.objects.create(exchange_short='NYSE',
                                       exchange_long='New York Stock Exchange',
                                       time_zone_name='CET',)

        apple = Stock.objects.create(symbol='AAPL',
                                     company='Apple',
                                     currency=usd,
                                     exchange=nyse,)

class IntraDayTests(PlotsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_intraday',
            kwargs={'source': 'quotes', 'symbol':'AAPL'})
        self.response = self.client.get(self.url)

    def test_intraday_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_intraday_view_incorrect_symbol_redirects(self):
        response = self.client.get(reverse('stock_intraday',
            kwargs={'source': 'quotes', 'symbol':'Goobliecook'}))
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
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '1'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_3(self):
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '3'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_5(self):
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '5'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_max(self):
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': 'max'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_response_contains_ref_to_worldtradingdata(self):
        self.assertEqual('www.worldtradingdata.com',
                         self.response.context['data_provider_url'])

        file_name = 'stock/tests/test_intraday.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(self.response.content.decode())

class HistoryTests(PlotsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '1'})
        self.response = self.client.get(self.url)

    def test_history_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '3'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '5'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': 'max'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

    def test_history_view_incorrect_symbol_redirects(self):
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'GooblieDoog', 'period': '1'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_history_view_incorrect_period_redirects(self):
        history_url = reverse('stock_history',
            kwargs={'source': 'quotes', 'symbol': 'AAPL', 'period': '2'})
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
        url = reverse('stock_intraday',
            kwargs={'source': 'quotes', 'symbol': symbol})
        self.assertContains(self.response, f'href="{url}"')

    def test_response_contains_ref_to_worldtradingdata(self):
        self.assertEqual('www.worldtradingdata.com',
                         self.response.context['data_provider_url'])

        file_name = 'stock/tests/test_history.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(self.response.content.decode())
