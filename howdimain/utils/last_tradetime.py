''' helper function to determine last trade time
'''
import datetime
import pytz
from stock.models import Exchange


def convert_timezone(timezone: str) -> str:
    ''' concvert time from database to pytz timezones
        for some known exceptions
    '''
    if timezone == 'JST':
        return 'Asia/Tokyo'

    elif timezone == 'KST':
        return 'Asia/Seoul'

    else:
        return timezone


def last_trade_time(trade_time: str, exchange_short: str) -> datetime:

    # try default option where tradetime is in a valid format
    try:
        return datetime.datetime.strptime(trade_time, '%Y-%m-%d %H:%M:%S')

    except ValueError:
        # otherwise base the last trade time on the current time in the exchange timezone
        try:
            exchange = Exchange.objects.get(exchange_short=exchange_short)

        except Exchange.DoesNotExist:
            return datetime.datetime(1963, 10, 22)

        try:
            timezone_stock = convert_timezone(exchange.time_zone_name.upper())

            _date_time = datetime.datetime.now(
                pytz.timezone(timezone_stock)).replace(tzinfo=None)
            _date_trade = datetime.datetime.strptime(trade_time, '%Y-%m-%d')

            trade_period = datetime.time(9, 0, 0) < _date_time.time() < datetime.time(18, 0, 0)  #pylint: disable=line-too-long
            date_is_today = _date_trade.date() == _date_time.date()
            if date_is_today and trade_period:
                pass

            else:
                _date_time = datetime.datetime.combine(
                    _date_trade.date(),
                    datetime.datetime.strptime('18:00:00', '%H:%M:%S').time()
                )

            return _date_time

        except ValueError:
            return datetime.datetime(1963, 10, 22)
