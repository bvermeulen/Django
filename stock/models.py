from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator


class Person(User):
    """this is a proxy for User"""

    class Meta:
        proxy = True

    def get_portfolio_names(self):
        return [
            p.portfolio_name for p in self.portfolios.all().order_by("portfolio_name")
        ]


class Currency(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    usd_exchange_rate = models.CharField(max_length=20, default="1.0")

    def get_exchangerate(self):
        return self.usd_exchange_rate

    def __str__(self):
        return str(self.currency)


class CurrencyHistory(models.Model):
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name="history"
    )
    currency_date = models.DateField()
    usd_exchange_rate_low = models.CharField(max_length=20, default="1.0")
    usd_exchange_rate_high = models.CharField(max_length=20, default="1.0")
    usd_exchange_rate = models.CharField(max_length=20, default="1.0")

    def __str__(self):
        return (
            f"{self.currency_date.strftime('%d-%m-%Y')}: "
            f"{self.currency.currency}, "
            f"{self.usd_exchange_rate}, "
            f"{self.usd_exchange_rate_low}, "
            f"{self.usd_exchange_rate_high}"
        )


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
        Currency, on_delete=models.CASCADE, related_name="exchanges"
    )

    def __str__(self):
        return str(self.name)


class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    symbol_ric = models.CharField(max_length=20, unique=True)
    company = models.CharField(max_length=75, unique=False)
    type = models.CharField(max_length=10, blank=True, null=True, default=None)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    exchange = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="stocks"
    )

    def mic(self):
        return self.exchange.mic

    def ric(self):
        return self.exchange.ric

    def __str__(self):
        return Truncator(self.company).chars(20)


class Portfolio(models.Model):
    portfolio_name = models.CharField(max_length=20)
    user = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="portfolios"
    )

    class Meta:
        unique_together = ["portfolio_name", "user"]

    def get_stock(self) -> dict:
        return {stock.stock.symbol_ric: stock.quantity for stock in self.stocks.all()}

    def __str__(self) -> str:
        return f"{self.portfolio_name} for {self.user.username}"


class StockSelection(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=20, default=0.0)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="stocks"
    )

    class Meta:
        unique_together = ["stock", "portfolio"]

    def __str__(self):
        return (
            f"{self.portfolio.user.username}, {self.portfolio.portfolio_name}: "
            f"{self.stock.symbol}, {self.quantity}"
        )


class StockHistory(models.Model):
    stock_selection = models.ForeignKey(
        StockSelection, on_delete=models.CASCADE, related_name="history"
    )
    trading_date = models.DateField()
    symbol = models.CharField(max_length=20, default="")
    quantity = models.CharField(max_length=20, default=0.0)
    open = models.CharField(max_length=20, default=0.0)
    latest_price = models.CharField(max_length=20, default=0.0)
    day_low = models.CharField(max_length=20, default=0.0)
    day_high = models.CharField(max_length=20, default=0.0)
    volume = models.CharField(max_length=20, default=0.0)
    close_yesterday = models.CharField(max_length=20, default=0.0)
    change_pct = models.CharField(max_length=20, default=0.0)
    day_change = models.CharField(max_length=20, default=0.0)

    class Meta:
        unique_together = ["stock_selection", "trading_date"]

    def __str__(self):
        return (
            f"{self.stockselection.portfolio.portfolio_name}, {self.stockselection.stock.symbol}\n"
            f"last trading time: {self.trading_datetime.strftime('%d-%m-%Y %H:%M')}\n"
            f"close yesterday: {self.close_yesterday}, open: {self.open}, price: {self.latest_price}, \n"
            f"day_low: {self.day_low}, day_high: {self.day_high}, volume: {self.volume}, \n"
            f"change: {self.day_change}, percentage: {self.change_pct}\n"
        )
