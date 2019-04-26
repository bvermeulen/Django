from django.urls import path
from newsfeed import views

urlpatterns = [
    path('news/', views.newspage, name='newspage'),
    path('news/mynewsitems', views.mynewsitems, name='mynewsitems'),
    path('news/sites/', views.newssites, name='newssites'),
    ]
