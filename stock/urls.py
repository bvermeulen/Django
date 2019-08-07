from django.urls import path
from stock import views

urlpatterns = [
    path('stock/stock_quote', views.QuoteView.as_view(), name='stock_quote'),
    path('stock/stock_intraday', views.IntraDayView.as_view(), name='stock_intraday'),
]
