import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator


class Person(User):
    """this is a proxy for User"""

    class Meta:
        proxy = True

    def get_portfolio_names(self) -> list[str]:
        return [
            p.portfolio_name for p in self.portfolios.all().order_by("portfolio_name")
        ]


class Currency(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    usd_exchange_rate = models.CharField(max_length=20, default="1.0")

    def get_exchangerate(self) -> str:
        return self.usd_exchange_rate

    def get_exchangerate_on_date(self, currency_date: str) -> str:
        if currency_date:
            currency = self.history.filter(currency_date=currency_date)
            return currency.last().usd_exchange_rate if currency else self.usd_exchange_rate

        else:
            return self.usd_exchange_rate

    def __str__(self) -> str:
        return str(self.currency)


class CurrencyHistory(models.Model):
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name="history"
    )
    currency_date = models.DateField()
    usd_exchange_rate_low = models.CharField(max_length=20, default="1.0")
    usd_exchange_rate_high = models.CharField(max_length=20, default="1.0")
    usd_exchange_rate = models.CharField(max_length=20, default="1.0")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self) -> str:
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

    def __str__(self) -> str:
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

    def mic(self) -> str:
        return self.exchange.mic

    def ric(self) -> str:
        return self.exchange.ric

    def __str__(self) -> str:
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

    def get_stock_on_date(self, trading_date: str) -> dict:
        return {stock.stock_history.stock.symbol_ric: stock.quantity for stock in self.history.filter(trading_date=trading_date)}

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

    def __str__(self) -> str:
        return (
            f"{self.portfolio.user.username}, {self.portfolio.portfolio_name}: "
            f"{self.stock.symbol}, {self.quantity}"
        )


class StockHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='history')
    last_trading_time = models.DateTimeField()
    open = models.CharField(max_length=20, default=0.0)
    latest_price = models.CharField(max_length=20, default=0.0)
    day_low = models.CharField(max_length=20, default=0.0)
    day_high = models.CharField(max_length=20, default=0.0)
    volume = models.CharField(max_length=20, default=0.0)
    close_yesterday = models.CharField(max_length=20, default=0.0)
    change_pct = models.CharField(max_length=20, default=0.0)
    day_change = models.CharField(max_length=20, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ["stock", "last_trading_time"]

    def __str__(self) -> str:
        return (
            f"\n{self.stock.symbol_ric}:\n"
            f"last trading time: {self.last_trading_time.strftime("%d-%m-%Y %H:%M")}\n"
            f"close yesterday: {self.close_yesterday}, open: {self.open}, price: {self.latest_price}, \n"
            f"day_low: {self.day_low}, day_high: {self.day_high}, volume: {self.volume}, \n"
            f"change: {self.day_change}, percentage: {self.change_pct}\n"
        )


class PortfolioHistory(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='history')
    trading_date = models.DateField()
    quantity = models.CharField(max_length=20, default=0.0)
    stock_history = models.ForeignKey(StockHistory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ["portfolio", "stock_history"]

    def __str__(self) -> str:
        return (
            f"\nPortfolio {self.portfolio.portfolio_name} on {self.trading_date.strftime("%d-%m-%Y")}\n"
            f"{self.quantity} {self.stock_history.stock.symbol_ric}, last price: {self.stock_history.latest_price}"
        )
