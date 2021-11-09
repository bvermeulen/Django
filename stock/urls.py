from django.urls import path
from stock.views import quotes, portfolios, plots, news

urlpatterns = [
    path('finance/stock_quote/', quotes.QuoteView.as_view(), name='stock_quotes'),

    path('finance/stock_news/<str:source>/<str:symbol>/',
         news.StockNewsView.as_view(), name='stock_news'),

    path('finance/stock_press/<str:source>/<str:symbol>/',
         news.StockPressView.as_view(), name='stock_press'),

    path('finance/stock_intraday/<str:source>/<str:symbol>/',
         plots.IntraDayView.as_view(), name='stock_intraday'),

    path('finance/stock_history/<str:source>/<str:symbol>/<str:period>/',
         plots.HistoryView.as_view(), name='stock_history'),

    path('finance/portfolio/', portfolios.PortfolioView.as_view(), name='portfolio'),
]
