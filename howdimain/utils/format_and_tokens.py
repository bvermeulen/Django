''' Functions for display tokens
'''
import decimal
from decimal import Decimal as d
from howdimain.howdimain_vars import CARET_UP, CARET_DOWN, CARET_NO_CHANGE

def add_display_tokens(orig_stock_info):
    ''' if there is stock info add display attributes for carets and color
    '''
    stock_info = []
    for stock in orig_stock_info:

        try:
            _ = float(stock.get('change_pct'))

        except ValueError:
            stock['change_pct'] = '0'

        if abs(float(stock.get('change_pct'))) < 0.001:
            stock['font_color'] = 'black'
            stock['caret_up_down'] = CARET_NO_CHANGE

        elif float(stock.get('change_pct')) < 0:
            stock['font_color'] = 'red'
            stock['caret_up_down'] = CARET_DOWN

        else:
            stock['font_color'] = 'green'
            stock['caret_up_down'] = CARET_UP

        stock_info.append(stock)

    return stock_info


def format_decimal_number(number):
    ''' Arguments:
        number: string, for example '1.0' or 'n/a'
        Returns:
        number: string - formatted
        If number is not a valid decimal then number is passed unchanged
    '''
    try:
        if d(number) > 1000:
            number = f'{d(number):,.0f}'

        else:
            number = f'{d(number):,.2f}'

    except decimal.InvalidOperation:
        pass

    return number


def format_and_sort_stocks(stocks):
    ''' format keys: value, value_change, price, day_low, day_high, close_yesterday
        sort stock on name with index stocks first
    '''
    _stocks = []
    _stocks_index = []
    for stock in stocks:
        try:
            stock['value'] = format_decimal_number(stock['value'])

        except KeyError:
            pass

        try:
            stock['value_change'] = format_decimal_number(stock['value_change'])

        except KeyError:
            pass

        try:
            stock['price'] = format_decimal_number(stock['price'])

        except KeyError:
            pass

        try:
            stock['day_change'] = format_decimal_number(stock['day_change'])

        except KeyError:
            pass

        try:
            stock['change_pct'] = format_decimal_number(stock['change_pct'])

        except KeyError:
            pass

        try:
            stock['day_low'] = format_decimal_number(stock['day_low'])

        except KeyError:
            pass

        try:
            stock['day_high'] = format_decimal_number(stock['day_high'])

        except KeyError:
            pass

        try:
            stock['close_yesterday'] = format_decimal_number(stock['close_yesterday'])

        except KeyError:
            pass

        if stock['symbol'][0] == '^' or stock['currency'] == 'N/A':
            _stocks_index.append(stock)

        else:
            _stocks.append(stock)

    if _stocks_index:
        _stocks_index = sorted(_stocks_index, key=lambda x: x['name'].lower())

    if _stocks:
        _stocks = sorted(_stocks, key=lambda x: x['name'].lower())

    return _stocks_index + _stocks


def format_totals_values(total_value, total_value_change):
    ''' returns a dict for totals for context display'''
    try:
        if abs(float(d(total_value_change))) < 0.1:
            color = 'black'
            caret = CARET_NO_CHANGE

        elif float(d(total_value_change)) < 0:
            color = 'red'
            caret = CARET_DOWN

        else:
            color = 'green'
            caret = CARET_UP

    except decimal.InvalidOperation:
        color = 'black'
        caret = CARET_NO_CHANGE

    total_value = format_decimal_number(total_value)
    total_value_change = format_decimal_number(total_value_change)

    return {'value': total_value, 'value_change': total_value_change,
            'caret': caret, 'color': color}
