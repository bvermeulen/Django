from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator


class Person(User):
    ''' this is a proxy for User
    '''
    class Meta:
        proxy = True

    def get_portfolio_names(self):
        return [
            p.portfolio_name for p in self.portfolios.all().order_by('portfolio_name')]


class Currency(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    usd_exchange_rate = models.CharField(max_length=20, default='1.0')

    def get_exchangerate(self):
        return self.usd_exchange_rate

    def __str__(self):
        return str(self.currency)


class Exchange(models.Model):
    mic = models.CharField(max_length=5, unique=True)
    ric = models.CharField(max_length=5, unique=False, default=None)
    name = models.CharField(max_length=50, unique=True)
    acronym = models.CharField(max_length=15, unique=True)
    country_code = models.CharField(max_length=5, unique=False)
    city = models.CharField(max_length=20, unique=False)
    website = models.CharField(max_length=50, unique=False)
    timezone = models.CharField(max_length=30)
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name='exchanges')

    def __str__(self):
        return str(self.name)


class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    symbol_ric = models.CharField(max_length=20, unique=True)
    company = models.CharField(max_length=75, unique=False)
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE)
    exchange = models.ForeignKey(
        Exchange, on_delete=models.CASCADE)

    def __str__(self):
        return Truncator(self.company).chars(20)


class Portfolio(models.Model):
    portfolio_name = models.CharField(max_length=20)
    user = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='portfolios')

    class Meta:
        unique_together = ['portfolio_name', 'user']

    def get_stock(self) -> list:
        return [stock.stock.symbol_ric for stock in self.stocks.all()]

    def __str__(self):
        return f'{self.portfolio_name} for {self.user.username}'

class StockSelection(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=20, default=1.0)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE,
                                  related_name='stocks')

    class Meta:
        unique_together = ['stock', 'portfolio']

    def __str__(self):
        return f'{self.portfolio.user.username}, {self.portfolio.portfolio_name}: '\
               f'{self.stock.symbol}, {self.quantity}'
