from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.news import StockNewsView, StockPressView
from ..models import Currency, Exchange, Stock


class NewsTestCase(TestCase):

    def setUp(self):
        self.test_user_name = "test_user"
        self.test_user_pw = "123"

        _ = User.objects.create_user(
            username=self.test_user_name,
            email="test@howdiweb.nl",
            password=self.test_user_pw,
        )

        _ = User.objects.create_user(
            username="default_user",
            email="default_user@howdiweb.nl",
            password="1234",
        )

        usd = Currency.objects.create(
            currency="USD",
            usd_exchange_rate="1.0",
        )

        nyse = Exchange.objects.create(
            mic="NYSE",
            ric="None",
            acronym="NYSE",
            name="New York Stock Exchange",
            timezone="America/New_York",
            currency=usd,
            country_code="US",
            city="New York",
            website="www.nyse.com",
        )

        _ = Stock.objects.create(
            symbol="AAPL",
            symbol_ric="AAPL",
            company="Apple",
            type="Stock",
            currency=usd,
            exchange=nyse,
        )


class StockNewsTests(NewsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("stock_news", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.response = self.client.get(self.url)

    def test_csrf_not_set(self):
        self.assertNotContains(self.response, "csrfmiddlewaretoken")

    def test_stocknews_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_stocknews_view_incorrect_symbol_message(self):
        response = self.client.get(
            reverse("stock_news", kwargs={"source": "quotes", "symbol": "Goobliecook"})
        )
        self.assertContains(response, "Alas, there is no news ...")

    def test_stocknews_url_resolves_stocknewsview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, StockNewsView)

    def test_stocknews_view_contains_link_to_home(self):
        home_url = reverse("home")
        self.assertContains(self.response, f'href="{home_url}"')

    def test_stocknews_view_contains_link_to_quotes(self):
        quotes_url = reverse("stock_quotes")
        self.assertContains(self.response, f'href="{quotes_url}"')

    def test_stocknews_view_contains_link_to_portfolio(self):
        url = reverse("stock_news", kwargs={"source": "portfolio", "symbol": "AAPL"})
        local_response = self.client.get(url)
        portfolio_url = reverse("portfolio")
        self.assertContains(local_response, f'href="{portfolio_url}"')

    def test_stocknews_views_contains_link_to_link(self):
        self.assertContains(self.response, "link")

    def test_stocknews_views_contains_link_to_graphs(self):
        url = reverse("stock_intraday", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.assertContains(self.response, f'href="{url}"')

    def test_stocknews_views_contains_link_to_return(self):
        self.assertContains(self.response, "Return")

    def test_stocknews_views_contains_link_to_press(self):
        url = reverse("stock_press", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.assertContains(self.response, f'href="{url}"')

    def test_stocknews_output_template(self):
        file_name = "stock/tests/test_stock_news.html"
        with open(file_name, "wt", encoding="utf-8") as f:
            f.write(self.response.content.decode())


class StockPressTests(NewsTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("stock_press", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.response = self.client.get(self.url)

    def test_csrf_not_set(self):
        self.assertNotContains(self.response, "csrfmiddlewaretoken")

    def test_stockpress_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_stockpress_view_incorrect_symbol_message(self):
        response = self.client.get(
            reverse(
                "stock_press", kwargs={"source": "quotes", "symbol": "Goobliecook"}
            )
        )
        self.assertContains(response, "Alas, there are no press releases ...")

    def test_stockpress_url_resolves_stockpressview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.view_class, StockPressView)

    def test_stockpress_view_contains_link_to_home(self):
        home_url = reverse("home")
        self.assertContains(self.response, f'href="{home_url}"')

    def test_stockpress_view_contains_link_to_quotes(self):
        quotes_url = reverse("stock_quotes")
        self.assertContains(self.response, f'href="{quotes_url}"')

    def test_stockpress_view_contains_link_to_portfolio(self):
        url = reverse("stock_press", kwargs={"source": "portfolio", "symbol": "AAPL"})
        local_response = self.client.get(url)
        portfolio_url = reverse("portfolio")
        self.assertContains(local_response, f'href="{portfolio_url}"')

    def test_stockpress_views_contains_link_to_link(self):
        self.assertContains(self.response, "link")

    def test_stockpress_views_contains_link_to_graphs(self):
        url = reverse("stock_intraday", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.assertContains(self.response, f'href="{url}"')

    def test_stockpress_views_contains_link_to_return(self):
        self.assertContains(self.response, "Return")

    def test_stockpress_views_contains_link_to_news(self):
        url = reverse("stock_news", kwargs={"source": "quotes", "symbol": "AAPL"})
        self.assertContains(self.response, f'href="{url}"')

    def test_stockpress_output_template(self):
        file_name = "stock/tests/test_stock_press.html"
        with open(file_name, "wt", encoding="utf-8") as f:
            f.write(self.response.content.decode())
