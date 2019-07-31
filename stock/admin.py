from django.contrib import admin
from .models import Exchange, Stock, Currency, Portfolio, StockSelection

admin.site.register(Exchange)
admin.site.register(Stock)
admin.site.register(Currency)
admin.site.register(Portfolio)
admin.site.register(StockSelection)
