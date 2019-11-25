import os

def populate_stock():
    import stock.module_stock
    stock_populate = stock.module_stock.PopulateStock()
    # filename = './stock/stock info/worldtradingdata-stocklist.csv'
    # stock_populate.read_csv(filename)
    # stock_populate.exchanges_and_currencies()
    # stock_populate.symbols()
    stock_populate.create_default_portfolios()


if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'howdimain.settings')
    django.setup()
    populate_stock()
