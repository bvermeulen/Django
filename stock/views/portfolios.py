import datetime
import json
from enum import Enum
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from howdimain.howdimain_vars import BASE_CURRENCIES, STOCK_DETAILS
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import (
    add_display_tokens,
    format_totals_values,
    format_and_sort_stocks,
)
from stock.models import Person, Stock, Portfolio, StockSelection
from stock.forms import PortfolioForm
from stock.module_stock import TradingData


logger = Logger.getlogger()
d = Decimal
source = "portfolio"


class GetStock(Enum):
    NO = 0
    YES = 1
    EMPTY = 3


@method_decorator(login_required, name="dispatch")
class PortfolioView(View):

    portfolio_form = PortfolioForm
    template_name = "finance/stock_portfolio.html"
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request):
        currency = request.session.get("currency", BASE_CURRENCIES[0][0])
        stockdetail = request.session.get("stockdetail", STOCK_DETAILS[0][0])
        selected_portfolio = request.session.get("selected_portfolio", "")
        datepicked = datetime.datetime.now().strftime("%d/%m/%Y")
        request.session["datepicked"] = datepicked
        user = request.user
        # add Person class to user
        if user.is_authenticated:
            user.__class__ = Person

        portfolio_name = ""
        stocks = []
        if selected_portfolio:
            try:
                self.portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=selected_portfolio
                )
                portfolio_name = self.portfolio.portfolio_name
                stocks = self.get_stock_info(request, GetStock.YES, currency)
                request.session["stock_info"] = json.dumps(
                    stocks, cls=DjangoJSONEncoder
                )
            except Portfolio.DoesNotExist:
                pass

        form = self.portfolio_form(
            user=user,
            initial={
                "symbol": "",
                "portfolio_name": portfolio_name,
                "portfolios": selected_portfolio,
                "currencies": currency,
                "stockdetails": stockdetail,
                "datepicked": datepicked,
            },
        )
        totals_values = format_totals_values(*self.td.calculate_stocks_value(stocks))
        stocks = add_display_tokens(stocks)
        stocks = format_and_sort_stocks(stocks)
        context = {
            "form": form,
            "stocks": stocks,
            "totals": totals_values,
            "source": source,
            "exchangerate": self.td.get_usd_euro_exchangerate(currency),
            "data_provider_url": self.data_provider_url,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        # add Person class to user
        if user.is_authenticated:
            user.__class__ = Person

        date_today = datetime.datetime.now().date().strftime("%d/%m/%Y")
        currency = request.session.get("currency", BASE_CURRENCIES[0][0])
        stockdetail = request.session.get("stockdetail", STOCK_DETAILS[0][0])
        datepicked = request.session.get("datepicked", date_today)

        form = self.portfolio_form(request.POST, user=user)
        if form.is_valid():
            previous_currency = currency
            previous_datepicked = datepicked
            form_data = form.cleaned_data
            currency = form_data.get("currencies")
            datepicked = form_data.get("datepicked").strftime("%d/%m/%Y")
            stockdetail = form_data.get("stockdetails")
            self.selected_portfolio = form_data.get("portfolios")
            self.portfolio_name = form_data.get("portfolio_name")
            self.new_portfolio = form_data.get("new_portfolio")
            self.symbol = form_data.get("symbol").upper()
            self.btn1_pressed = form_data.get("btn1_pressed")
            self.change_qty_btn_pressed = form_data.get("change_qty_btn_pressed")
            self.delete_symbol_btn_pressed = form_data.get("delete_symbol_btn_pressed")

            self.previous_selected = request.session.get("selected_portfolio")
            datepicked = (
                datepicked
                if datepicked
                and not (
                    self.btn1_pressed
                    or self.delete_symbol_btn_pressed
                    or self.change_qty_btn_pressed
                )
                else date_today
            )
            get_stock = (
                GetStock.YES
                if self.previous_selected != self.selected_portfolio
                or previous_currency != currency
                or previous_datepicked != datepicked
                else GetStock.NO
            )
            try:
                self.portfolio = Portfolio.objects.get(
                    user=user, portfolio_name=self.selected_portfolio
                )
            except Portfolio.DoesNotExist:
                self.portfolio = None
                self.selected_portfolio = ""
                self.btn1_pressed = ""
                get_stock = GetStock.EMPTY

            match self.btn1_pressed:
                case "new_portfolio":
                    get_stock = self.create_new_portfolio(user)

                case "rename_portfolio":
                    get_stock = self.rename_portfolio()

                case "copy_portfolio":
                    get_stock = self.copy_portfolio()

                case "delete_portfolio":
                    get_stock = self.delete_portfolio()

                case "add_symbol":
                    get_stock = self.add_symbol()

                case _:
                    pass

            if self.change_qty_btn_pressed:
                get_stock = self.change_quantity_symbol()

            if self.delete_symbol_btn_pressed:
                get_stock = self.delete_symbol()

            # set portfolio name except if the portfolio has been deleted or does not exist
            try:
                self.portfolio_name = self.portfolio.portfolio_name

            except AttributeError:
                self.portfolio_name = ""

            dateval_query = (
                datetime.datetime.strptime(datepicked, "%d/%m/%Y").strftime("%Y-%m-%d")
                if datepicked != date_today
                else None
            )
            stocks = self.get_stock_info(request, get_stock, currency, dateval_query)
            request.session["stock_info"] = json.dumps(stocks, cls=DjangoJSONEncoder)
            request.session["selected_portfolio"] = self.selected_portfolio
            request.session["currency"] = currency
            request.session["stockdetail"] = stockdetail
            request.session["datepicked"] = datepicked

            form = self.portfolio_form(
                user=user,
                initial={
                    "portfolio_name": self.portfolio_name,
                    "portfolios": self.selected_portfolio,
                    "symbol": self.symbol,
                    "currencies": currency,
                    "stockdetails": stockdetail,
                    "datepicked": datepicked,
                },
            )
            logger.info(
                f"user {user} [ip: {get_client_ip(request)}] "
                f"views {self.selected_portfolio}"
            )
        else:
            form = self.portfolio_form(
                user=user,
                initial={
                    "portfolios": "",
                    "portfolio_name": "",
                    "symbol": "",
                    "currencies": currency,
                    "stockdetails": stockdetail,
                    "datepicked": date_today,
                },
            )
            stocks = []

        totals_values = format_totals_values(*self.td.calculate_stocks_value(stocks))
        stocks = add_display_tokens(stocks)
        stocks = format_and_sort_stocks(stocks)
        context = {
            "form": form,
            "stocks": stocks,
            "totals": totals_values,
            "source": source,
            "exchangerate": self.td.get_usd_euro_exchangerate(currency),
            "data_provider_url": self.data_provider_url,
        }
        return render(request, self.template_name, context)

    def create_new_portfolio(self, user: Person) -> GetStock:
        if not self.new_portfolio:
            return GetStock.NO

        try:
            self.portfolio = Portfolio.objects.create(
                user=user, portfolio_name=self.new_portfolio
            )
            self.selected_portfolio = self.new_portfolio
            return GetStock.EMPTY

        except IntegrityError:
            # patch in case initial choice portfolios is None then for some reason
            # choicefield will return the first option. In that case reset all
            if not self.previous_selected:
                self.portfolio = None
                self.selected_portfolio = self.previous_selected
                return GetStock.EMPTY

            else:
                self.new_portfolio = ""
                return GetStock.NO

    def rename_portfolio(self) -> GetStock:
        if (
            not self.portfolio
            or not self.portfolio_name
            or self.portfolio_name == self.selected_portfolio
        ):
            logger.warning(f"{self.portfolio}: check rename portfolio")
            return GetStock.NO

        try:
            self.portfolio.portfolio_name = self.portfolio_name
            self.portfolio.save()
            self.selected_portfolio = self.portfolio_name

        except IntegrityError:
            pass

        return GetStock.YES

    def copy_portfolio(self) -> GetStock:
        if not self.portfolio:
            logger.warning(f"{self.portfolio}: check existance of portfolio")
            return GetStock.NO

        if self.new_portfolio == self.selected_portfolio:
            return GetStock.NO

        symbols_quantities = self.portfolio.get_stock()
        try:
            self.portfolio.portfolio_name = self.new_portfolio
            self.portfolio.pk = None
            self.portfolio.save()
            self.selected_portfolio = self.new_portfolio

        except IntegrityError:
            return GetStock.NO

        for symbol, quantity in symbols_quantities.items():
            try:
                StockSelection.objects.create(
                    stock=Stock.objects.get(symbol_ric=symbol),
                    quantity=quantity,
                    portfolio=self.portfolio,
                )
            except (Stock.DoesNotExist, IntegrityError, ValueError):
                pass

        return GetStock.YES

    def delete_portfolio(self) -> GetStock:
        if not self.portfolio:
            logger.warning(f"{self.portfolio}: check existance of portfolio")
            return GetStock.NO

        self.portfolio.delete()
        self.portfolio = None
        self.selected_portfolio = ""
        self.portfolio_name = ""
        return GetStock.EMPTY

    def add_symbol(self) -> GetStock:
        if not self.portfolio:
            logger.warning(f"{self.portfolio}: check existance of portfolio")
            return GetStock.NO

        try:
            StockSelection.objects.create(
                stock=Stock.objects.get(symbol_ric=self.symbol),
                quantity=0,
                portfolio=self.portfolio,
            )
            self.symbol = ""
            return GetStock.YES

        except (Stock.DoesNotExist, IntegrityError, ValueError):
            return GetStock.YES

    def change_quantity_symbol(self) -> GetStock:
        if not self.portfolio:
            logger.warning(f"{self.portfolio}: check existance of portfolio")
            return GetStock.NO

        try:
            symbol, quantity = self.change_qty_btn_pressed.split(",")
            symbol = symbol.strip()
            quantity = quantity.strip()

        except ValueError:
            return GetStock.NO

        selected_stock = self.portfolio.stocks.get(stock__symbol_ric=symbol)
        if selected_stock.stock.currency.currency != "N/A":
            selected_stock.quantity = quantity
            selected_stock.save()
            return GetStock.YES

        else:
            return GetStock.NO

    def delete_symbol(self) -> GetStock:
        if not self.portfolio:
            logger.warning(f"{self.portfolio}: check existance of portfolio")
            return GetStock.NO

        self.portfolio.stocks.get(
            stock__symbol_ric=self.delete_symbol_btn_pressed
        ).delete()

        return GetStock.YES

    def get_stock_info(
        self, request, get_stock: GetStock, currency: str, datepicked: str = None
    ):
        stocks = []
        if not self.portfolio:
            return stocks

        match get_stock:
            case GetStock.YES:
                stocks = self.td.get_portfolio_stock_info(
                    self.portfolio, currency, trading_date=datepicked
                )
                request.session["stock_info"] = json.dumps(
                    stocks, cls=DjangoJSONEncoder
                )

            case GetStock.NO:
                try:
                    stocks = json.loads(request.session.get("stock_info"))
                except TypeError:
                    stocks = self.td.get_portfolio_stock_info(
                        self.portfolio, currency, trading_date=datepicked
                    )

            case GetStock.EMPTY:
                # stocks is empty list already fullfilled
                pass

            case _:
                logger.warning(f"invalid selection for get_stock: {get_stock}")

        return stocks
