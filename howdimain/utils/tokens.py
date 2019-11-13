''' Functions for display tokens
'''
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
