from django.urls import path
from newsfeed.views import newspage, mynewsitems, newssites

urlpatterns = [
    path('news/', newspage.newspage, name='newspage'),
	path('news/mynewsitems/', mynewsitems.MyNewsItems.as_view(), name='mynewsitems'),
    path('news/sites/', newssites.newssites, name='newssites'),
]
