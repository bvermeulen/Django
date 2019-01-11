import feedparser
import time
import re
from django.contrib.auth.models import User
from .models import NewsSite, UserNewsSite
from django.db.utils import IntegrityError
from django.core import serializers

news_list = {'CNN World News':
             'http://rss.cnn.com/rss/edition_world.rss',
             'The Guardian':
             'https://www.theguardian.com/business/economics/rss',
             'NOS algemeen':
             'http://feeds.nos.nl/nosnieuwsalgemeen',
             'Nu.nl':
             'http://www.nu.nl/rss/Algemeen',
             'BBC World News':
             'http://feeds.bbci.co.uk/news/world/rss.xml',
             'BBC Technology':
             'http://feeds.bbci.co.uk/news/technology/rss.xml',
             'BBC Business':
             'http://feeds.bbci.co.uk/news/business/rss.xml',
             'Hacker fp':
             'https://hnrss.org/frontpage',
             'Django':
             'https://hnrss.org/newest?q=Django',
             'Thailand':
             'https://tradingeconomics.com/thailand/rss',
             'Mad Money':
             'https://www.cnbc.com/id/15838459/device/rss/rss.html',
             }

def update_news(news_url):
    '''  Function to update the news and display the news site
    '''
    return feedparser.parse(news_url)["items"]


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

    for selectednewssite in ['BBC World News']:
        newssite = NewsSite.objects.get(news_site=selectednewssite)
        usersites.news_sites.add(newssite)
        usersites.save()

    for user in User.objects.all():
        for newssite in NewsSite.objects.filter(usernewssite__user=user):
            print(f'User {user.username}: {newssite.news_url}')