import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "howdimain.settings")
import datetime
from zoneinfo import ZoneInfo
import django

django.setup()
from stock.module_stock import TradingData
from stock.models import Portfolio, StockHistory, Stock, StockSelection
from django.db.utils import IntegrityError
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED
from howdimain.utils.tradetime import get_exchange_timezone

td = TradingData()
td.setup()


def update_stock_history():
    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        # split cash components
        symbols = portfolio.get_stock()
        list_symbols = list(symbols.keys())
        cash_symbols = []
        for cash_stock in td.cash_stocks:
            if cash_stock in list_symbols:
                list_symbols.remove(cash_stock)
                cash_symbols.append(cash_stock)

        stock_info = td.get_stock_trade_info(list_symbols[0:MAX_SYMBOLS_ALLOWED])
        stock_info += td.get_stock_trade_info(
            list_symbols[MAX_SYMBOLS_ALLOWED : 2 * MAX_SYMBOLS_ALLOWED]
        )
        stock_info += td.get_cash_trade_info(cash_symbols)
        for stock in stock_info:
            stock_object = Stock.objects.get(symbol_ric=stock["symbol"])
            portfolio_stock_selection = StockSelection.objects.get(
                portfolio=portfolio, stock=stock_object
            )
            exchange_timezone = get_exchange_timezone(stock_object.exchange.mic)
            datetime_now_at_exchange = (
                datetime.datetime.now(ZoneInfo(exchange_timezone))
            ).replace(tzinfo=None)
            datetime_stock = stock["last_trade_time"]

            if datetime_now_at_exchange > datetime_stock + datetime.timedelta(hours=1):
                try:
                    StockHistory.objects.create(
                        stock_selection=portfolio_stock_selection,
                        last_trading_date=datetime_stock,
                        symbol=stock["symbol"],
                        quantity=symbols[stock["symbol"]],
                        open=stock["open"],
                        latest_price=stock["price"],
                        day_low=stock["day_low"],
                        day_high=stock["day_high"],
                        volume=stock["volume"],
                        close_yesterday=stock["close_yesterday"],
                        change_pct=stock["change_pct"],
                        day_change=stock["day_change"],
                    )
                except IntegrityError:
                    pass  # already created


def main():

    update_stock_history()


if __name__ == "__main__":
    main()
