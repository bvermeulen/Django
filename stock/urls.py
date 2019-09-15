from django.urls import path
from stock.views import quotes, portfolios

urlpatterns = [
    path('finance/stock_quote/', quotes.QuoteView.as_view(), name='stock_quotes'),
    path('finance/stock_intraday/<str:symbol>/',
         quotes.IntraDayView.as_view(), name='stock_intraday'),
    path('finance/stock_history/<str:symbol>/<str:period>/',
         quotes.HistoryView.as_view(), name='stock_history'),

    path('finance/portfolio/', portfolios.PortfolioView.as_view(), name='portfolio'),
]
