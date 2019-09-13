from django.urls import path
from stock.views import quote_view, portfolio_view

urlpatterns = [
    path('finance/stock_quote', quote_view.QuoteView.as_view(), name='stock_quotes'),
    path('finance/stock_intraday/<str:symbol>/',
         quote_view.IntraDayView.as_view(), name='stock_intraday'),
    path('finance/stock_history/<str:symbol>/<str:period>/',
         quote_view.HistoryView.as_view(), name='stock_history'),

    path('finance/portfolio/', portfolio_view.PortfolioView.as_view(), name='portfolio'),
]
