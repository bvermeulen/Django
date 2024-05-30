import datetime
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from howdimain.howdimain_vars import URL_FMP
from ..models import Person, Currency, Exchange, Stock, StockSelection, Portfolio
from ..views.quotes import QuoteView

URL_PROVIDER = URL_FMP


class QuotesTestSetup(TestCase):

    def setUp(self):
        self.test_user = "test_user"
        self.test_user_pw = "123"
        self.default_user = "default_user"

        test_user = User.objects.create_user(
            username=self.test_user,
            email="test@howdiweb.nl",
            password=self.test_user_pw,
        )

        default_user = User.objects.create_user(
            username="default_user", email="default@howdiweb.nl", password="456"
        )

        usd = Currency.objects.create(currency="USD", usd_exchange_rate="1.0")

        eur = Currency.objects.create(currency="EUR", usd_exchange_rate="0.9")

        nyse = Exchange.objects.create(
            mic="XNYS",
            ric="None",
            acronym="NYSE",
            name="New York Stock Exchange",
            currency=usd,
            timezone="America/New_York",
            country_code="US",
            city="New York",
            website="www.nyse.com",
        )

        aex = Exchange.objects.create(
            mic="XAMS",
            ric="AS",
            name="Amsterdam AEX",
            currency=eur,
            timezone="Europe/Amsterdam",
            country_code="NL",
            city="Amsterdam",
            website="www.aex.com",
        )

        apple = Stock.objects.create(
            symbol="AAPL",
            symbol_ric="AAPL",
            company="Apple",
            type="stock",
            currency=usd,
            exchange=nyse,
        )

        asml = Stock.objects.create(
            symbol="ASML.XAMS",
            symbol_ric="ASML.AS",
            company="ASML Holding",
            type="stock",
            currency=eur,
            exchange=aex,
        )

        Stock.objects.create(
            symbol="WKL.XAMS",
            symbol_ric="WKL.AS",
            company="Wolters Kluwer",
            type="stock",
            currency=eur,
            exchange=aex,
        )

        test_portfolio = Portfolio.objects.create(
            portfolio_name="test_portfolio",
            user=test_user,
        )

        StockSelection.objects.create(
            stock=apple,
            quantity=10,
            portfolio=test_portfolio,
        )

        default_aex = Portfolio.objects.create(
            portfolio_name="AEX_index",
            user=default_user,
        )

        StockSelection.objects.create(
            stock=asml,
            quantity=1,
            portfolio=default_aex,
        )


class QuotesViewGetTests(QuotesTestSetup):

    def test_quotes_view_status_code(self):
        response = self.client.get(reverse("stock_quotes"))
        self.assertEqual(response.status_code, 200)

    def test_quotes_url_resolves_QuoteView(self):
        view = resolve("/finance/stock_quote/")
        self.assertEqual(view.func.view_class, QuoteView)

    def test_quote_view_contains_link_to_home(self):
        response = self.client.get(reverse("stock_quotes"))
        home_url = reverse("home")
        self.assertContains(response, f'href="{home_url}"')

    def test_response_contains_csrf_token(self):
        response = self.client.get(reverse("stock_quotes"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_correct_number_input_tags(self):
        """
        8 <input> tags to be found:
        csrf token
        quote_string
        selected_portfolio
        markets XNAS
        markets XNYS
        Graphs
        News
        Press
        """
        response = self.client.get(reverse("stock_quotes"))
        self.assertContains(response, "<input", 8)

    def test_not_logged_does_not_give_my_portfolio(self):
        response = self.client.get(reverse("stock_quotes"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "My Portfolio")

    def test_response_contains_ref_to_url_provider(self):
        response = self.client.get(reverse("stock_quotes"))
        self.assertEqual(URL_PROVIDER, response.context["data_provider_url"])
        file_name = "stock/tests/test_quotes.html"
        with open(file_name, "wt", encoding="utf-8") as f:
            f.write(response.content.decode())


class QuotesViewPostTests(QuotesTestSetup):

    data = {
        "markets": ["XAMS"],
        "stockdetails": "Graphs",
        "datepicked_pressed": "false",
        "datepicked": datetime.datetime.now().date().strftime("%d/%m/%Y"),
    }

    def test_valid_quote_string_returns_stock_info(self):
        self.data.update({
            "quote_string": "kluwer",
            "selected_portfolio": "",
            "portfolios": "",
        })
        url = reverse("stock_quotes")
        response = self.client.post(url, self.data)
        self.assertEqual("WKL.AS", response.context["stock_info"][0]["symbol"])

    def test_valid_quote_string_has_a_link_to_intraday_view(self):
        self.data.update(
            {
                "quote_string": "kluwer",
                "selected_portfolio": "",
                "portfolios": "",
            }
        )
        url = reverse("stock_quotes")
        response = self.client.post(url, self.data)
        self.assertContains(response, 'href="/finance/stock_intraday/quotes/WKL.AS/"')

    def test_invalid_quote_string_returns_empty_stock_info(self):
        self.data.update(
            {
                "quote_string": "Goobliecook",
                "selected_portfolio": "",
                "portfolios": "",
            }
        )
        url = reverse("stock_quotes")
        response = self.client.post(url, self.data)
        self.assertEqual(True, not response.context["stock_info"])

    def test_select_portfolio_returns_stock_info(self):
        self.data.update(
            {
                "quote_string": "",
                "selected_portfolio": "",
                "portfolios": "AEX_index",
            }
        )
        url = reverse("stock_quotes")
        response = self.client.post(url, self.data)
        self.assertEqual("ASML.AS", response.context["stock_info"][0]["symbol"])

    def test_user_portfolio_returns_stock_info(self):
        self.client.login(username=self.test_user, password=self.test_user_pw)
        self.data.update(
            {
                "quote_string": "",
                "selected_portfolio": "",
                "portfolios": "test_portfolio",
            }
        )
        url = reverse("stock_quotes")
        response = self.client.post(url, self.data)
        self.assertEqual("AAPL", response.context["stock_info"][0]["symbol"])
