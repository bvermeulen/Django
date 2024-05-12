import datetime
import decimal
from collections import namedtuple
import requests
from decouple import config
from howdimain.howdimain_vars import MAX_SYMBOLS_ALLOWED, PLOT_PERIODS
from howdimain.utils.tradetime import tradetime_fromstring
from howdimain.utils.format_and_tokens import calc_change
from howdimain.utils.plogger import Logger
from howdimain.utils.pagination_marketstack import pagination_marketstack_threaded
from stock.models import Stock


logger = Logger.getlogger()
api_token = config("access_key_marketstack")
marketstack_api_url = "https://api.marketstack.com/v1/"
d = decimal.Decimal


def convert_stock_symbols(symbols_ric: list) -> list:

    symbols_mic = []
    for symbol_ric in symbols_ric:
        try:
            symbols_mic.append(Stock.objects.get(symbol_ric=symbol_ric).symbol)

        except Stock.DoesNotExist:
            pass

    return symbols_mic


def get_stock_marketstack(stock_symbols: list) -> dict:
    """return the stock trade info as a dict"""
    stock_symbols = convert_stock_symbols(stock_symbols)

    symbols = ",".join(stock_symbols).upper()
    stock_url = marketstack_api_url + "eod/latest"
    params = {
        "symbols": symbols,
        "access_key": api_token,
    }

    stock_list = []
    if stock_symbols:
        try:
            res = requests.get(stock_url, params=params)
            if res and res.status_code == 200:
                stock_list = res.json().get("data")
            else:
                pass

        except requests.exceptions.ConnectionError:
            logger.warning(f"connection error: {stock_url} {params}")

    else:
        pass

    if len(stock_symbols) > MAX_SYMBOLS_ALLOWED:
        logger.warning(f"number of symbols exceed maximum of {MAX_SYMBOLS_ALLOWED}")

    stock_info = []
    for quote in stock_list:

        # res.json() has return [[]] therefor check if element is actually a dict
        if not isinstance(quote, dict):
            continue

        stock_dict = {}
        # get currency and exchange info from the database if it does not exist
        # skip this quote
        try:
            stock_db = Stock.objects.get(symbol=quote["symbol"])

        except Stock.DoesNotExist:
            continue

        s_open = quote.get("open")
        s_close = quote.get("close")
        s_change, s_change_pct = calc_change(s_open, s_close)

        stock_dict["currency"] = stock_db.currency.currency
        stock_dict["exchange_mic"] = stock_db.exchange.mic
        stock_dict["symbol"] = stock_db.symbol_ric
        stock_dict["name"] = stock_db.company
        stock_dict["open"] = s_open
        stock_dict["day_high"] = quote.get("high")
        stock_dict["day_low"] = quote.get("low")
        stock_dict["price"] = s_close
        stock_dict["volume"] = quote.get("volume")
        stock_dict["close_yesterday"] = s_open
        stock_dict["day_change"] = s_change
        stock_dict["change_pct"] = s_change_pct
        stock_dict["last_trade_time"] = tradetime_fromstring(
            quote.get("date"), stock_dict["exchange_mic"]
        )
        stock_info.append(stock_dict)

    symbols = ", ".join([stock["symbol"] for stock in stock_info])
    if stock_info:
        logger.info(f"marketstack symbols: {symbols}")

    return stock_info


def get_intraday_marketstack(symbol: str) -> list:
    """marketstack intraday quotes are on the Investors Exchange (IEXG) and
    not implemented as yet, they should be covered by Financial Modeling Prep
    """
    return []


def get_history_marketstack(symbol_ric, period):
    trade = namedtuple("trade", "date open close low high volume")
    symbol = symbol_ric.upper()
    symbol = convert_stock_symbols([symbol])
    history_url = marketstack_api_url + "eod"

    if period == PLOT_PERIODS[-1]:
        set_total = None

    else:
        set_total = int(float(period) * 365)

    history_series = pagination_marketstack_threaded(
        history_url, api_token, symbol, set_total
    )

    # create list of trade_info tuples
    history_trades = []
    for trade_info in history_series:
        history_trades.append(
            trade(
                date=datetime.datetime.strptime(
                    trade_info.get("date")[0:10], "%Y-%m-%d"
                ),
                open=trade_info.get("open"),
                close=trade_info.get("high"),
                low=trade_info.get("low"),
                high=trade_info.get("close"),
                volume=trade_info.get("volume"),
            )
        )

    if history_trades:
        logger.info(f"marketstack history: {symbol_ric}")

    else:
        logger.warning(
            f"marketstack history: unable to get stock history data for "
            f"{history_url} {symbol_ric}"
        )

    return history_trades
