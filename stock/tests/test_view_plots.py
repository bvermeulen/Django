from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from howdimain.howdimain_vars import URL_FMP
from ..views.plots import IntraDayView, HistoryView
from ..models import Currency, Exchange, Stock

URL_PROVIDER = URL_FMP

class PlotsTestCase(TestCase):

    def setUp(self):
        self.test_user_name = 'test_user'
        self.test_user_pw = '123'

        _ = User.objects.create_user(
            username=self.test_user_name,
            email='test@howdiweb.nl',
            password=self.test_user_pw,
        )

        _ = User.objects.create_user(
            username='default_user',
            email='default_user@howdiweb.nl',
            password='1234',
        )

        usd = Currency.objects.create(
            currency='USD',
            usd_exchange_rate='1.0',
        )

        nyse = Exchange.objects.create(
            mic='NYSE',
            ric='None',
            acronym='NYSE',
            name='New York Stock Exchange',
            timezone='America/New_York',
            currency=usd,
            country_code='US',
            city='New York',
            website='www.nyse.com',
        )

        _ = Stock.objects.create(
            symbol='AAPL',
            symbol_ric='AAPL',
            company='Apple',
            type="Stock",
            currency=usd,
            exchange=nyse,
        )


class IntraDayTests(PlotsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_intraday', kwargs={
            'source': 'quotes', 'symbol':'AAPL'})
        self.response = self.client.get(self.url)

    def test_csrf_not_set(self):
        self.assertNotContains(self.response, "csrfmiddlewaretoken")

    def test_intraday_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_intraday_view_incorrect_symbol_redirects(self):
        response = self.client.get(reverse('stock_intraday', kwargs={
            'source': 'quotes', 'symbol':'Goobliecook'}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_intraday_url_resolves_intradayView(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, IntraDayView)

    def test_intraday_view_contains_link_to_home(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_intraday_view_contains_link_to_quotes(self):
        quotes_url = reverse('stock_quotes')
        self.assertContains(self.response, f'href="{quotes_url}"')

    def test_intraday_view_contains_link_to_portfolio(self):
        url = reverse('stock_intraday', kwargs={
            'source': 'portfolio', 'symbol':'AAPL'})
        local_response = self.client.get(url)
        portfolio_url = reverse('portfolio')
        self.assertContains(local_response, f'href="{portfolio_url}"')

    def test_intraday_view_contains_link_to_history_0_5(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '0.5'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_1(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '1'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_3(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '3'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_history_max(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': 'max'})
        self.assertContains(self.response, f"href='{history_url}'")

    def test_intraday_view_contains_link_to_stock_press(self):
        news_url = reverse(
            "stock_press",
            kwargs={"source": "quotes", "symbol": "AAPL"},
        )
        self.assertContains(self.response, f"href='{news_url}'")

    def test_intraday_view_contains_link_to_stock_news(self):
        news_url = reverse(
            "stock_news",
            kwargs={"source": "quotes", "symbol": "AAPL"},
        )
        self.assertContains(self.response, f"href='{news_url}'")

    def test_response_contains_ref_to_url_provider(self):
        self.assertEqual(URL_PROVIDER, self.response.context['data_provider_url'])
        file_name = 'stock/tests/test_intraday.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(self.response.content.decode())

class HistoryTests(PlotsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '1'})
        self.response = self.client.get(self.url)

    def test_csrf_not_set(self):
        self.assertNotContains(self.response, "csrfmiddlewaretoken")

    def test_history_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_history_view_contains_link_to_intraday(self):
        symbol = self.response.context["stock_symbol"]
        url = reverse("stock_intraday", kwargs={"source": "quotes", "symbol": symbol})
        self.assertContains(self.response, f'href="{url}"')

    def test_history_view_contains_link_to_history_0_5(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '0.5'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

    def test_history_view_contains_link_to_history_3(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '3'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

    def test_history_view_contains_link_to_history_max(self):
        history_url = reverse(
            "stock_history",
            kwargs={"source": "quotes", "symbol": "AAPL", "period": "max"},
        )
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

    def test_history_view_contains_link_to_stock_press(self):
        news_url = reverse(
            "stock_press",
            kwargs={"source": "quotes", "symbol": "AAPL"},
        )
        self.assertContains(self.response, f"href='{news_url}'")

    def test_history_view_contains_link_to_stock_news(self):
        news_url = reverse(
            "stock_news",
            kwargs={"source": "quotes", "symbol": "AAPL"},
        )
        self.assertContains(self.response, f"href='{news_url}'")

    def test_history_view_incorrect_symbol_redirects(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'GooblieDoog', 'period': '1'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_history_view_incorrect_period_redirects(self):
        history_url = reverse('stock_history', kwargs={
            'source': 'quotes', 'symbol': 'AAPL', 'period': '2'})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stock_quotes'))

    def test_intraday_url_resolves_historyview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, HistoryView)

    def test_history_view_contains_link_to_home(self):
        url = reverse('home')
        self.assertContains(self.response, f'href="{url}"')

    def test_history_view_contains_link_to_quotes(self):
        url = reverse('stock_quotes')
        self.assertContains(self.response, f'href="{url}"')

    def test_history_view_contains_link_to_portfolio(self):
        url = reverse('stock_history', kwargs={
            'source': 'portfolio', 'symbol':'AAPL', 'period': '1'})
        local_response = self.client.get(url)
        portfolio_url = reverse('portfolio')
        self.assertContains(local_response, f'href="{portfolio_url}"')

    def test_response_contains_ref_to_url_provider(self):
        self.assertEqual(URL_PROVIDER, self.response.context['data_provider_url'])
        file_name = 'stock/tests/test_history.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(self.response.content.decode())
