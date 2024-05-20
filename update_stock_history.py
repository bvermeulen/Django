import os
import contextlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "howdimain.settings")
import datetime
from zoneinfo import ZoneInfo
import django

django.setup()
from stock.module_stock import TradingData
from stock.models import Portfolio, Stock, StockHistory, PortfolioHistory
from django.db.utils import IntegrityError
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED
from howdimain.utils.tradetime import get_exchange_timezone
from howdimain.utils.plogger import Logger

td = TradingData()
td.setup()
logger = Logger.getlogger()


def update_stock_history():
    portfolios = Portfolio.objects.all()
    counter = 0
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
            exchange_timezone = get_exchange_timezone(stock_object.exchange.mic)
            datetime_now_at_exchange = (
                datetime.datetime.now(ZoneInfo(exchange_timezone))
            ).replace(tzinfo=None)
            datetime_stock = stock["last_trade_time"]

            # check if the stock has not been updated for 4 hours, then it is assumed the exchange is closed
            if datetime_now_at_exchange > datetime_stock + datetime.timedelta(hours=4):
                if not StockHistory.objects.filter(
                    stock=stock_object, last_trading_time=datetime_stock
                ).exists():
                    StockHistory.objects.create(
                        stock=stock_object,
                        last_trading_time=datetime_stock,
                        open=stock["open"],
                        latest_price=stock["price"],
                        day_low=stock["day_low"],
                        day_high=stock["day_high"],
                        volume=stock["volume"],
                        close_yesterday=stock["close_yesterday"],
                        change_pct=stock["change_pct"],
                        day_change=stock["day_change"],
                    )

                stock_history = StockHistory.objects.get(
                    stock=stock_object, last_trading_time=datetime_stock
                )
                if not PortfolioHistory.objects.filter(
                    portfolio=portfolio, stock_history=stock_history
                ).exists():
                    PortfolioHistory.objects.create(
                        portfolio=portfolio,
                        trading_date=datetime_stock.date(),
                        quantity=symbols[stock["symbol"]],
                        stock_history=stock_history,
                    )
                    counter += 1

    logger.info(f"System updated history for {counter} stocks")


if __name__ == "__main__":
    update_stock_history()
