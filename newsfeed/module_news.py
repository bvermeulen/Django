import re
import requests
from datetime import datetime, timezone
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
import feedparser
from .models import NewsSite, UserNewsSite

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
             'SLB':
             'https://www.slb.com/news/press_releases.aspx?r=1',
             }


def update_news(news_url):
    '''  Function to update the news and display the news site
    '''
    raw = ''
    try:
        response = requests.get(news_url)

        if response and response.status_code == 200:
            raw = response.text

        else:
            pass

    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        pass

    # if raw <item>'s have a '<image> ... </image>' pattern extract the image url and
    # put this image url in an <enclosure /> tag which can be handled by feedparser
    raw = re.sub(r'(<item>.*?)<image>.*?(http.*?jpg|png|gif).*?</image>(.*?</item>)',
                 r'\1<enclosure url="\2" />\3', raw)

    # some url give an empty raw string, in that case parse with the url instead of
    # the raw string
    if raw:
        parser = feedparser.parse(raw)

    else:
        parser = feedparser.parse(news_url)

    return parser.entries


def remove_feedburner_reference(summary):
    feedburner_reference = r'<.*src="http://feeds\.feedburner\.com.*?>'
    return re.sub(feedburner_reference, '', summary)


def feedparser_time_to_datetime(feed_item):
    ''' Converts the feedparser parsed time (published_parsed or
        updated_parsed) [a python time tuple] to a datetime object. If there is
        no parsed time, the current time is taken
        Parameter:
        :feed_item: dictionary with either published_parsed or updated_parsed
        Return:
        :news_published: datetime object with converted time
    '''
    try:
        news_published = datetime(*feed_item.published_parsed[0:6])
    except AttributeError:
        try:
            news_published = datetime(*feed_item.updated_parsed[0:6])
        except AttributeError:
            news_published = datetime.now()

    return news_published.replace(tzinfo=timezone.utc)


def restore_sort_feedparserdict(feed_items):
    ''' restore feed items to FeedParserDict - for some reason Django sessions
        converts them to Dict; sort by date
        :arguments: list of news item dicts
        :returns: dictionary of news items dicts
    '''
    # first restore feed_item list to a feedparser dict
    feed_items = [feedparser.FeedParserDict(feed_item) for feed_item in feed_items]

    # sort the feed_items list on date
    feed_items_sorted = []
    for feed_item in feed_items:
        feed_items_sorted.append((feed_item, feedparser_time_to_datetime(feed_item)))

    feed_items_sorted.sort(key=lambda k: k[1], reverse=True)

    # now make the new feedparser dict
    new_feed_items = {}
    for i, feed_item in enumerate(feed_items_sorted):
        new_feed_items[i] = feed_item[0]

    return new_feed_items


def remove_all_references(summary):
    return re.sub(r'<.*?>', '', summary)


def add_news_site_to_model():
    ''' Function to add news_site to the NewsSite model
    '''
    existing_newssites = [entry['news_site'] for entry in
                          NewsSite.objects.values('news_site')]
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
        print('User has already a selection')

    for selectednewssite in ['BBC World News']:
        newssite = NewsSite.objects.get(news_site=selectednewssite)
        usersites.news_sites.add(newssite)
        usersites.save()

    for user in User.objects.all():
        for newssite in NewsSite.objects.filter(usernewssite__user=user):
            print(f'User {user.username}: {newssite.news_url}')
