import datetime
from django.contrib.auth.models import User
from decimal import Decimal
from django.urls import reverse, resolve
from django.test import TestCase
from howdimain.howdimain_vars import URL_FMP
from ..views.portfolios import PortfolioView
from ..models import (
    Currency,
    Exchange,
    Stock,
    StockSelection,
    Portfolio,
    CurrencyHistory,
    StockHistory,
    PortfolioHistory,
)

URL_PROVIDER = URL_FMP
d = Decimal


class PortfolioTestSetup(TestCase):

    def setUp(self):
        self.history_datetime = datetime.datetime(
            2024, 8, 20, 16, 35, 00, tzinfo=datetime.timezone.utc
        )
        self.test_user_name = "test_user"
        self.test_user_pw = "123"

        self.test_user = User.objects.create_user(
            username=self.test_user_name,
            email="test@howdiweb.nl",
            password=self.test_user_pw,
        )
        usd = Currency.objects.create(
            currency="USD",
            usd_exchange_rate="1.0",
        )
        eur = Currency.objects.create(
            currency="EUR",
            usd_exchange_rate="0.9",
        )
        CurrencyHistory.objects.create(
            currency=eur,
            currency_date=self.history_datetime.date(),
            usd_exchange_rate_low="0.85",
            usd_exchange_rate_high="0.92",
            usd_exchange_rate="0.88",
        )
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
        self.apple = Stock.objects.create(
            symbol="AAPL",
            symbol_ric="AAPL",
            company="Apple",
            type="stock",
            currency=usd,
            exchange=nyse,
        )
        self.asml = Stock.objects.create(
            symbol="ASML.XAMS",
            symbol_ric="ASML.AS",
            company="ASML HOLDING",
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
        apple_hist = StockHistory.objects.create(
            stock=self.apple,
            last_trading_time=self.history_datetime,
            open="130.0",
            latest_price="131.4",
            day_low="128.1",
            day_high="132.2",
            volume="1100300",
            close_yesterday="130.5",
            change_pct="0.685",
            day_change="0.9",
        )
        asml_hist = StockHistory.objects.create(
            stock=self.asml,
            last_trading_time=self.history_datetime,
            open="250.0",
            latest_price="245.1",
            day_low="239.2",
            day_high="252.8",
            volume="21522",
            close_yesterday="250.5",
            change_pct="-2.156",
            day_change="-5.4",
        )
        self.test_portfolio = Portfolio.objects.create(
            portfolio_name="test_portfolio",
            user=self.test_user,
        )
        StockSelection.objects.create(
            stock=self.apple,
            quantity=10,
            portfolio=self.test_portfolio,
        )
        PortfolioHistory.objects.create(
            portfolio=self.test_portfolio,
            trading_date=self.history_datetime.date(),
            quantity="20",
            stock_history=asml_hist,
        )
        PortfolioHistory.objects.create(
            portfolio=self.test_portfolio,
            trading_date=self.history_datetime.date(),
            quantity="300",
            stock_history=apple_hist,
        )
        self.client.login(username=self.test_user_name, password=self.test_user_pw)

        self.data = {
            "currencies": "USD",
            "date_is_today": True,
            "datepicked": datetime.datetime.now().date().strftime("%d/%m/%Y"),
            "stockdetails": "Graphs",
        }


class PortfolioViewGetTests(PortfolioTestSetup):

    def test_portfolio_view_status_code(self):
        response = self.client.get(reverse("portfolio"))
        self.assertEqual(response.status_code, 200)

    def test_url_resolves_PortfolioView(self):
        view = resolve("/finance/portfolio/")
        self.assertEqual(view.func.view_class, PortfolioView)

    def test_view_contains_link_to_home(self):
        response = self.client.get(reverse("portfolio"))
        home_url = reverse("home")
        self.assertContains(response, f'href="{home_url}"')

    def test_view_contains_link_to_quotes(self):
        response = self.client.get(reverse("portfolio"))
        quotes_url = reverse("stock_quotes")
        self.assertContains(response, f'href="{quotes_url}"')

    def test_response_contains_csrf_token(self):
        response = self.client.get(reverse("portfolio"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_correct_number_input_tags(self):
        """
        5 <input> tags to be found:
        csrf token (2x), new_portfolio, portfolio_name, symbol,
        """
        response = self.client.get(reverse("portfolio"))
        self.assertContains(response, "<input", 5)

    def test_select_portfolio(self):
        s = self.client.session
        s.update(
            {
                "selected_portfolio": "test_portfolio",
                "currency": "USD",
                "stockdetail": "graph",
            }
        )
        s.save()
        response = self.client.get(reverse("portfolio"))
        self.assertEqual("AAPL", response.context["stocks"][0]["symbol"])

    def test_response_contains_ref_to_url_provider(self):
        response = self.client.get(reverse("portfolio"))
        self.assertEqual(URL_PROVIDER, response.context["data_provider_url"])

    def test_not_logged_in_redirects_to_login_page(self):
        self.client.logout()
        response = self.client.get(reverse("portfolio"))
        login_url = reverse("login") + f'?next={reverse("portfolio")}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)


class PortfolioViewPostTests(PortfolioTestSetup):

    def test_new_portfolio(self):
        url = reverse("portfolio")
        self.data.update(
            {
                "new_portfolio": "my_new_portfolio",
                "btn1_pressed": "new_portfolio",
            }
        )
        self.client.post(url, self.data)
        self.assertEqual(2, len(Portfolio.objects.filter(user=self.test_user)))

    def response_post(self, data):
        self.data.update(data)
        return self.client.post(reverse("portfolio"), self.data)

    def test_delete_portfolio(self):
        Portfolio.objects.create(user=self.test_user, portfolio_name="my_new_portfolio")
        data = {
            "btn1_pressed": "delete_portfolio",
            "portfolios": "my_new_portfolio",
            "portfolio_name": "my_new_portfolio",
        }
        _ = self.response_post(data)
        self.assertEqual(1, len(Portfolio.objects.filter(user=self.test_user)))

    def test_rename_portfolio(self):
        Portfolio.objects.create(user=self.test_user, portfolio_name="my_new_portfolio")
        data = {
            "btn1_pressed": "rename_portfolio",
            "portfolios": "my_new_portfolio",
            "portfolio_name": "HAHA MAIN",
        }
        response = self.response_post(data)
        self.assertEqual(
            1,
            len(
                Portfolio.objects.filter(
                    user=self.test_user, portfolio_name="HAHA MAIN"
                )
            ),
        )
        self.assertEqual(
            "HAHA MAIN", response.context["form"]["portfolio_name"].value()
        )
        self.assertEqual("HAHA MAIN", response.context["form"]["portfolios"].value())

    def test_add_symbol(self):
        data = {
            "portfolios": "test_portfolio",
            "portfolio_name": "test_portfolio",
            "btn1_pressed": "add_symbol",
            "symbol": "ASML.AS",
        }
        response = self.response_post(data)
        stocks_portfolio_db = (
            Portfolio.objects.filter(
                user=self.test_user, portfolio_name="test_portfolio"
            )
            .first()
            .stocks.all()
        )
        self.assertEqual(2, len(stocks_portfolio_db))
        self.assertEqual("ASML.AS", stocks_portfolio_db[1].stock.symbol_ric)
        self.assertEqual("ASML.AS", response.context["stocks"][1]["symbol"])

    def test_link_to_intraday_view(self):
        data = {
            "portfolios": "test_portfolio",
            "portfolio_name": "test_portfolio",
        }
        response = self.response_post(data)
        self.assertContains(response, 'href="/finance/stock_intraday/portfolio/AAPL/"')

    def test_add_invalid_symbol(self):
        data = {
            "portfolios": "test_portfolio",
            "btn1_pressed": "add_symbol",
            "symbol": "HAHAHA",
        }
        response = self.response_post(data)
        stocks_portfolio_db = (
            Portfolio.objects.filter(
                user=self.test_user, portfolio_name="test_portfolio"
            )
            .first()
            .stocks.all()
        )
        self.assertEqual(1, len(stocks_portfolio_db))
        self.assertEqual("AAPL", stocks_portfolio_db[0].stock.symbol)
        self.assertEqual(1, len(response.context["stocks"]))

    def test_change_quantity(self):
        data = {
            "portfolios": "test_portfolio",
            "change_qty_btn_pressed": "AAPL, 5",
        }
        response = self.response_post(data)
        aapl = StockSelection.objects.filter(
            stock=self.apple, portfolio=self.test_portfolio
        )
        self.assertEqual("5", aapl.first().quantity)
        self.assertEqual("5", response.context["stocks"][0]["quantity"])

    def test_delete_stock(self):
        # first add a new symbol to the portfolio
        StockSelection.objects.create(
            stock=self.asml, quantity=0, portfolio=self.test_portfolio
        )
        data = {
            "portfolios": "test_portfolio",
            "delete_symbol_btn_pressed": "ASML.AS",
        }
        response = self.response_post(data)
        stocks_portfolio_db = (
            Portfolio.objects.filter(
                user=self.test_user, portfolio_name="test_portfolio"
            )
            .first()
            .stocks.all()
        )
        self.assertEqual(1, len(stocks_portfolio_db))
        self.assertEqual("AAPL", stocks_portfolio_db[0].stock.symbol)
        self.assertEqual("AAPL", response.context["stocks"][0]["symbol"])

    def test_portfolio_euro_value(self):
        data = {
            "portfolios": "test_portfolio",
            "currencies": "EUR",
        }
        response = self.response_post(data)
        stocks_value = d(response.context["totals"]["value"].replace(",", ""))
        value_eur = 0
        for stock in response.context["stocks"]:
            value_eur += d(stock["value"].replace(",", ""))

        self.assertEqual(
            stocks_value.quantize(d("0.01")), value_eur.quantize(d("0.01"))
        )

    def test_portfolio_usd_value(self):
        data = {
            "portfolios": "test_portfolio",
        }
        response = self.response_post(data)
        stocks_value = d(response.context["totals"]["value"].replace(",", ""))
        value_usd = 0
        for stock in response.context["stocks"]:
            value_usd += d(stock["quantity"]) * d(stock["price"].replace(",", ""))

        if value_usd > 1000:
            value_usd = d(f"{value_usd:.0f}")

        else:
            value_usd = d(f"{value_usd:.2f}")

        self.assertEqual(
            stocks_value.quantize(d("0.01")), value_usd.quantize(d("0.01"))
        )

    def test_portfolio_value_change(self):
        data = {
            "portfolios": "test_portfolio",
        }
        response = self.response_post(data)
        stocks_value = d(response.context["totals"]["value_change"].replace(",", ""))

        value = 0
        for stock in response.context["stocks"]:
            value += d(stock["value_change"].replace(",", ""))

        self.assertEqual(stocks_value.quantize(d("0.01")), value.quantize(d("0.01")))

    def test_portfolio_contains_controls(self):
        data = {
            "portfolios": "test_portfolio",
        }
        response = self.response_post(data)
        self.assertContains(response, "ConfirmDeleteSymbol(", 2)
        self.assertContains(response, "ChangeQuantity(", 2),
        self.assertContains(response, "AddSymbol(", 2)
        self.assertContains(response, "PromptNewPortfolioName(", 2)
        self.assertContains(response, "RenamePortfolio(", 2)
        self.assertContains(response, "CopyPortfolio(", 2)
        self.assertContains(response, "ConfirmDeletePortfolio(", 2)
        self.assertContains(response, "dropdown-divider", 2)

    def test_history_portfolio_does_not_contain_controls(self):
        data = {
            "portfolios": "test_portfolio",
            "datepicked": self.history_datetime.date().strftime("%d/%m/%Y"),
            "date_is_today": False,
        }
        response = self.response_post(data)
        self.assertContains(response, "ConfirmDeleteSymbol(", 1)
        self.assertContains(response, "ChangeQuantity(", 1)
        self.assertContains(response, "AddSymbol(", 1)
        self.assertContains(response, "PromptNewPortfolioName(", 1)
        self.assertContains(response, "RenamePortfolio(", 1)
        self.assertContains(response, "CopyPortfolio(", 1)
        self.assertContains(response, "ConfirmDeletePortfolio(", 1)
        self.assertContains(response, "ConfirmDeletePortfolio(", 1)
        self.assertContains(response, "dropdown-divider", 1)

    def test_historic_portfolio_value(self):
        """ 300 apple @ USD 131.40 = 39420
             20 asml @ EUR 245.10 = 4902 @ (1/0.88) = 5570
            Total: 44990
        """
        data = {
            "portfolios": "test_portfolio",
            "datepicked": self.history_datetime.date().strftime("%d/%m/%Y"),
            "date_is_today": False,
        }
        response = self.response_post(data)
        stocks_value = d(response.context["totals"]["value"].replace(",", ""))
        self.assertEqual(stocks_value, 44990)

    def test_create_html(self):
        data = {
            "portfolios": "test_portfolio",
        }
        response = self.response_post(data)
        file_name = "stock/tests/test_portfolio.html"
        with open(file_name, "wt", encoding="utf-8") as f:
            f.write(response.content.decode())
