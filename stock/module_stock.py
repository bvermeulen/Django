from .models import Exchange, Currency, Stock
from django.db.utils import IntegrityError
import csv

class PopulateStock:

    def read_csv(cls, filename):
        cls.stock_data = []
        with open(filename) as csv_file:
            _stock_data = csv.reader(csv_file, delimiter=",")
            # skip the header
            next(_stock_data, None)
            for row in _stock_data:
                cls.stock_data.append(row)

    def exchanges_and_currencies(cls,):
        for i, row in enumerate(cls.stock_data):
            # print(f'processing row {i}, stock {row[1]}')
            try:
                Exchange.objects.create(
                    exchange_long=row[3],
                    exchange_short=row[4],
                    time_zone_name=row[5]
                )
            except IntegrityError:
                pass

            try:
                Currency.objects.create(
                    currency=row[2]
                )
            except IntegrityError:
                pass

    def symbols(cls,):
        for i, row in enumerate(cls.stock_data):
            if row[4] in ['AEX', 'NYSE', 'NASDAQ']:
                print(f'processing row {i}, stock {row[1]}')
                try:
                    stock = Stock.objects.create(
                                symbol=row[0],
                                company=row[1][0:75],
                                currency=Currency.objects.get(currency=row[2]),
                                exchange=Exchange.objects.get(exchange_short=row[4]),
                                )
                    stock.save()
                except IntegrityError:
                    print(f'already in database, stock: {row[1]}')
                    pass
