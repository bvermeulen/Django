from django.urls import path
from stock import views

urlpatterns = [
    path('finance/stock_quote', views.QuoteView.as_view(), name='stock_quotes'),
    path('finance/stock_intraday/<str:symbol>/', views.IntraDayView.as_view(), name='stock_intraday'),
    path('finance/stock_history/<str:symbol>/', views.HistoryView.as_view(), name='stock_history'),
    # path('finance/fusion_test/', fusion_test.chart, name='stock_fusion'),
]
