from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator


class Exchange(models.Model):
    exchange_short = models.CharField(max_length=15, unique=True)
    exchange_long = models.CharField(max_length=50, unique=False)
    time_zone_name = models.CharField(max_length=30)

    def __str__(self):
        return self.exchange_long


class Currency(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    usd_exchange_rate = models.CharField(max_length=20, default='1.0')

    def __str__(self):
        return self.currency


class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    company = models.CharField(max_length=75, unique=False)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE,
                                 related_name='stocks')
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE,
                                 related_name='stocks')

    def __str__(self):
        return Truncator(self.company).chars(20)


class Portfolio(models.Model):
    portfolio_name = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    class Meta:
        unique_together = ['portfolio_name', 'user']

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
