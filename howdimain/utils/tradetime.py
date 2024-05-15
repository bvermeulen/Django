""" helper function to determine last trade time
"""

import datetime
from zoneinfo import ZoneInfo
from stock.models import Exchange

default_exchange = "XNYS"
start_trade = datetime.time(9, 0)
end_trade = datetime.time(18, 0)


def get_exchange_timezone(exchange_mic: str) -> str:
    """convert time from database to pytz timezones
    for some known exceptions
    """
    try:
        exchange = Exchange.objects.get(mic=exchange_mic)

    except Exchange.DoesNotExist:
        exchange = Exchange.objects.get(mic=default_exchange)

    exchange_timezone = exchange.timezone.title()

    if exchange_timezone == "JST":
        return "Asia/Tokyo"

    elif exchange_timezone == "KST":
        return "Asia/Seoul"

    else:
        return exchange_timezone


def tradetime_fromtimestamp(timestamp: int, exchange_mic: str) -> datetime:
    #for invalid timestamp revert to 1 January 1980
    if timestamp == 0:
        timestamp = 315532800

    exchange_timezone = get_exchange_timezone(exchange_mic)
    return (
        datetime.datetime.fromtimestamp(timestamp).astimezone(
            ZoneInfo(exchange_timezone)
        )
    ).replace(tzinfo=None)


def tradetime_fromstring(trade_time: str, exchange_mic: str) -> datetime:
    # try default option where tradetime is in a valid format
    exchange_timezone = get_exchange_timezone(exchange_mic)
    try:
        return (
            datetime.datetime.strptime(trade_time, "%Y-%m-%d %H:%M:%S").astimezone(
                ZoneInfo(exchange_timezone)
            )
        ).replace(tzinfo=None)

    except ValueError:
        # otherwise base the last trade time on the current time in the exchange timezone

        try:
            _date_time = datetime.datetime.now(ZoneInfo(exchange_timezone))
            _date_trade = datetime.datetime.strptime(trade_time, "%Y-%m-%d")

            trade_period = (
                datetime.time(9, 0, 0) < _date_time.time() < datetime.time(18, 0, 0)
            )
            date_is_today = _date_trade.date() == _date_time.date()
            if date_is_today and trade_period:
                pass

            else:
                _date_time = datetime.datetime.combine(
                    _date_trade.date(),
                    datetime.datetime.strptime("18:00:00", "%H:%M:%S").time(),
                )
            return _date_time

        except ValueError:
            # return best guess which is end of day of the previous weekday, note bank
            # holidays are not dealt with
            _date_time = _date_time - datetime.timedelta(
                days=[3, 1, 1, 1, 1, 1, 2][_date_time.weekday()]
            )
            _date_time = datetime.datetime.combine(
                _date_time.date(),
                datetime.datetime.strptime("18:00:00", "%H:%M:%S").time(),
            )
            return _date_time
