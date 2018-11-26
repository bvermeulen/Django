import feedparser
import time
import re
from django.contrib.auth.models import User
from .models import NewsSite, UserNewsSite
from django.db.utils import IntegrityError


def update_news(news_url):
    '''  Function to update the news and display the news site
    '''
    return feedparser.parse(news_url)


def add_news_site_to_model():
    ''' Function to add news_site to the NewsSite model
    '''
    existing_newssites = [entry['news_site'] for entry in NewsSite.objects.values('news_site')]
    print(existing_newssites)

    for news_site, url in news_list.items():
        print(news_site, url)
        try:
            NewsSite.objects.create(news_site=news_site,
                                     news_url=url)
        except IntegrityError:
            print(f'news site {news_site} already exists')


def add_news_sites_to_default_user():
    default_user_name = 'default_user'
    user = User.objects.get(username=default_user_name)
    if user is None:
        raise Exception(f'No user named {default_user_name}')

    try:
        usersites = UserNewsSite(user=user)
        usersites.save()
    except IntegrityError:
        usersites = UserNewsSite.objects.get(user=user)
        print('User has already a selectection')

    for selectednewssite in ['Nu.nl', 'BBC World News', 'Mad Money']:
        newssite = NewsSite.objects.get(news_site=selectednewssite)
        usersites.news_sites.add(newssite)
        usersites.save()

    for user in User.objects.all():
        for newssite in NewsSite.objects.filter(usernewssite__user=user):
            print(f'User {user.username}: {newssite.news_url}')
