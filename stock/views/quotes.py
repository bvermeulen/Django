import datetime
from django.shortcuts import render
from django.views.generic import View
from stock.models import Person, Portfolio
from stock.module_stock import TradingData
from stock.forms import StockQuoteForm
from howdimain.howdimain_vars import MARKETS, STOCK_DETAILS, MAX_SYMBOLS_ALLOWED
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.format_and_tokens import add_display_tokens, format_and_sort_stocks
from howdimain.utils.plogger import Logger


logger = Logger.getlogger()
source = "quotes"


class QuoteView(View):
    stockquote_form = StockQuoteForm
    template_name = "finance/stock_quotes.html"
    td = TradingData()
    td.setup()
    data_provider_url = td.data_provider_url

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            # add Person class to user
            user.__class__ = Person

        selected_portfolio = request.session.get("selected_portfolio", "")
        stockdetail = request.session.get("stockdetail", STOCK_DETAILS[0][0])
        markets = request.session.get("markets", MARKETS)
        quote_string = ""
        datepicked = datetime.datetime.now().strftime("%d/%m/%Y")

        portfolio = self.select_portfolio(user, selected_portfolio)
        if portfolio:
            symbols = list(portfolio.get_stock().keys())
            stock_info = self.td.get_stock_trade_info(symbols[0:MAX_SYMBOLS_ALLOWED])
            stock_info += self.td.get_stock_trade_info(
                symbols[MAX_SYMBOLS_ALLOWED : 2 * MAX_SYMBOLS_ALLOWED]
            )
        else:
            symbols = self.td.parse_stock_quote(quote_string, markets=markets)
            stock_info = self.td.get_stock_trade_info(symbols[0:MAX_SYMBOLS_ALLOWED])
            selected_portfolio = ""

        form = self.stockquote_form(
            user=user,
            initial={
                "quote_string": quote_string,
                "portfolios": selected_portfolio,
                "markets": markets,
                "stockdetails": stockdetail,
                "datepicked": datepicked,
            },
        )
        stock_info = add_display_tokens(stock_info)
        stock_info = format_and_sort_stocks(stock_info)
        context = {
            "source": source,
            "stock_info": stock_info,
            "form": form,
            "data_provider_url": self.data_provider_url,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            # add Person class to user
            user.__class__ = Person

        date_today = datetime.datetime.now().date().strftime("%d/%m/%Y")
        quote_string = request.session.get("quote_string", "")
        selected_portfolio = request.session.get("selected_portfolio", "")
        datepicked = request.session.get("datepicked", date_today)
        markets = request.session.get("markets", MARKETS)
        stockdetail = request.session.get("stockdetail", STOCK_DETAILS[0][0])

        form = self.stockquote_form(request.POST, user=user)
        if form.is_valid():
            form_data = form.cleaned_data
            new_quote_string = form_data.get("quote_string")
            new_selected_portfolio = form_data.get("portfolios")
            markets = form_data.get("markets")
            stockdetail = form_data.get("stockdetails")
            datepicked_pressed = form_data.get("datepicked_pressed")

            if datepicked_pressed == "true":
                datepicked = form_data.get("datepicked").strftime("%d/%m/%Y")

            if new_selected_portfolio != selected_portfolio:
                selected_portfolio = new_selected_portfolio
                quote_string = ""

            elif new_quote_string != quote_string:
                quote_string = new_quote_string
                selected_portfolio = ""

            else:
                pass

            portfolio = self.select_portfolio(user, selected_portfolio)
            if portfolio and datepicked == date_today:
                symbols = list(portfolio.get_stock().keys())
                stock_info = self.td.get_stock_trade_info(
                    symbols[0:MAX_SYMBOLS_ALLOWED]
                )
                stock_info += self.td.get_stock_trade_info(
                    symbols[MAX_SYMBOLS_ALLOWED : 2 * MAX_SYMBOLS_ALLOWED]
                )

            elif portfolio:
                dateval_query = datetime.datetime.strptime(
                    datepicked, "%d/%m/%Y"
                ).strftime("%Y-%m-%d")
                symbols = list(portfolio.get_stock_on_date(dateval_query).keys())
                stock_info = self.td.get_stock_trade_info_on_date(
                    dateval_query, symbols
                )

            else:
                datepicked = date_today
                symbols = self.td.parse_stock_quote(quote_string, markets=markets)
                stock_info = self.td.get_stock_trade_info(
                    symbols[0:MAX_SYMBOLS_ALLOWED]
                )
                selected_portfolio = ""

            logger.info(
                f"user {user} [ip: {get_client_ip(request)}] looking "
                f"up: {quote_string} / {selected_portfolio}"
            )
        else:
            stock_info = []

        form = self.stockquote_form(
            user=user,
            initial={
                "quote_string": quote_string,
                "portfolios": selected_portfolio,
                "markets": markets,
                "stockdetails": stockdetail,
                "datepicked": datepicked,
            },
        )

        request.session["quote_string"] = quote_string
        request.session["selected_portfolio"] = selected_portfolio
        request.session["markets"] = markets
        request.session["stockdetail"] = stockdetail
        request.session["datepicked"] = datepicked

        stock_info = add_display_tokens(stock_info)
        stock_info = format_and_sort_stocks(stock_info)
        context = {
            "source": source,
            "stock_info": stock_info,
            "form": form,
            "data_provider_url": self.data_provider_url,
        }
        return render(request, self.template_name, context)

    def select_portfolio(self, user, selected_portfolio):
        portfolio = None
        if selected_portfolio:
            try:
                if user.is_authenticated:
                    portfolio = Portfolio.objects.get(
                        user=user, portfolio_name=selected_portfolio
                    )
                else:
                    raise Portfolio.DoesNotExist

            except Portfolio.DoesNotExist:
                try:
                    default_user = Person.objects.get(username="default_user")
                    portfolio = Portfolio.objects.get(
                        user=default_user, portfolio_name=selected_portfolio
                    )
                except (Person.DoesNotExist, Portfolio.DoesNotExist):
                    pass

        return portfolio
