''' helper function to determine last trade time
'''
import datetime
import pytz
from stock.models import Exchange

default_exchange = 'XNYS'
start_trade = datetime.time(9, 0)
end_trade = datetime.time(18,0)


def convert_timezone(timezone: str) -> str:
    ''' convert time from database to pytz timezones
        for some known exceptions
    '''
    if timezone == 'JST':
        return 'Asia/Tokyo'

    elif timezone == 'KST':
        return 'Asia/Seoul'

    else:
        return timezone


def trade_time(exchange_mic: str) -> datetime:
    ''' returns datetime of time of last trade, based on the following:
            - trade is on weekdays between start_trade and end_trade
            - if outside trading hours last trade time is given of the
              previous day or last day of week.
            - disregards bank holidays
    '''
    try:
        exchange = Exchange.objects.get(mic=exchange_mic)

    except Exchange.DoesNotExist:
        exchange = Exchange.objects.get(mic=default_exchange)

    timezone_exchange = convert_timezone(exchange.timezone.upper())
    date_time = datetime.datetime.now(
        pytz.timezone(timezone_exchange)).replace(tzinfo=None)

    date_trade = date_time.date()
    time_trade = date_time.time()

    if date_trade.isoweekday() == 6:
        date_trade -= datetime.timedelta(days=1)
        trade_date_time = datetime.datetime.combine(date_trade, end_trade)

    elif date_trade.isoweekday() == 7:
        date_trade -= datetime.timedelta(days=2)
        trade_date_time = datetime.datetime.combine(date_trade, end_trade)

    elif time_trade < start_trade:
        if date_trade.isoweekday() == 1:
            date_trade -= datetime.timedelta(days=3)

        else:
            date_trade -= datetime.timedelta(days=1)

        trade_date_time = datetime.datetime.combine(date_trade, end_trade)

    elif time_trade < end_trade:
        trade_date_time = date_time

    else:
        trade_date_time = datetime.datetime.combine(date_trade, end_trade)

    return trade_date_time


def last_trade_time(trade_time: str, exchange_mic: str) -> datetime:
    # try default option where tradetime is in a valid format
    try:
        return datetime.datetime.strptime(trade_time, '%Y-%m-%d %H:%M:%S')

    except ValueError:
        # otherwise base the last trade time on the current time in the exchange timezone
        try:
            exchange = Exchange.objects.get(mic=exchange_mic)

        except Exchange.DoesNotExist:
            exchange = Exchange.objects.get(mic=default_exchange)

        try:
            timezone_stock = convert_timezone(exchange.timezone.upper())

            _date_time = datetime.datetime.now(
                pytz.timezone(timezone_stock)).replace(tzinfo=None)
            _date_trade = datetime.datetime.strptime(trade_time, '%Y-%m-%d')

            trade_period = datetime.time(9, 0, 0) < _date_time.time() < datetime.time(18, 0, 0)  #pylint: disable=line-too-long
            date_is_today = _date_trade.date() == _date_time.date()
            if date_is_today and trade_period:
                pass

            else:
                _date_time = datetime.datetime.combine(
                    _date_trade.date(), datetime.datetime.strptime(
                        '18:00:00', '%H:%M:%S').time()
                )

            return _date_time

        except ValueError:
            # return best guess which is end of day of the previous weekday, note bank
            # holidays are not dealt with
            _date_time = _date_time - datetime.timedelta(
                days=[3, 1, 1, 1, 1, 1, 2][_date_time.weekday()])
            _date_time = datetime.datetime.combine(
                _date_time.date(), datetime.datetime.strptime(
                    '18:00:00', '%H:%M:%S').time()
            )

            return _date_time

