from django.urls import path
from newsfeed import views as news_views

urlpatterns = [
    path('news/', news_views.NewsFeed().newspage, name='newspage'),
    path('news/sites/', news_views.NewsFeed().newssites, name='newssites'),
    ]
