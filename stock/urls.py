from django.urls import path
from stock import views, fusion_test

urlpatterns = [
    path('stock/stock_quote', views.QuoteView.as_view(), name='stock_quote'),
    path('stock/stock_intraday/<str:symbol>/', views.IntraDayView.as_view(), name='stock_intraday'),
    path('stock/fusion_test/', fusion_test.chart, name='stock_fusion'),
]
