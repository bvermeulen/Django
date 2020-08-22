import os

def populate_stock():
    import stock.module_stock
    stock_populate = stock.module_stock.StockTools()
    filename_exchanges = './marketstack_exchanges.xlsx'
    # filename_stocks = './marketstack_stocks.xlsx'
    filename_stocks = './additional_stocks.xlsx'
    filename_portfolios = './stock info/user_portfolios.xlsx'


    # stock_populate.exchanges_and_currencies(filename_exchanges)
    # stock_populate.symbols(filename_stocks)
    stock_populate.create_portfolios(filename_portfolios, ric=False)
    # stock_populate.extract_portfolios('zz_test.xlsx')


if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'howdimain.settings')
    django.setup()
    populate_stock()
