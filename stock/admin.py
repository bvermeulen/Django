from django.contrib import admin
from .models import Exchange, Stock, Currency

admin.site.register(Exchange)
admin.site.register(Stock)
admin.site.register(Currency)
