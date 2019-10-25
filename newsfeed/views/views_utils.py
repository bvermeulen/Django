from pprint import pprint
import re
from recordtype import recordtype
from django.core.exceptions import ObjectDoesNotExist
from howdimain.utils.plogger import Logger
from howdimain.howdimain_vars import IMG_WIDTH
from ..models import NewsSite, UserNewsSite, UserNewsItem
from ..module_news import (feedparser_time_to_datetime,
                           remove_feedburner_reference, remove_all_references,
                          )


logger = Logger.getlogger()
NewsStatus = recordtype(
    'NewsStatus',
    'current_news_site news_site updated item news_items banner error_message')


def set_session_newsstatus(request, newsstatus):
    for key, value in newsstatus._asdict().items():
        request.session[key] = value


def get_session_newsstatus(request):
    ns_keys = NewsStatus(*[None]*7)
    return NewsStatus(*[request.session[key] for key, _ in ns_keys._asdict().items()])


def store_news_item(user, ns, feed_items, ip):
    ''' store news item to model UserNewsItem
        arguments:
        :user: user (type model User)
        :ns: newstatus (type recordtype)
        :feed_items: feed items (feedparser dict type)
        :ip: ip address (type string)
    '''
    link = feed_items[ns.item].link
    usernewsitem = UserNewsItem.objects.filter(user=user).filter(link=link).first()
    news_published = feedparser_time_to_datetime(feed_items[ns.item])
    if usernewsitem and usernewsitem.published < news_published:
        usernewsitem.delete()
        usernewsitem = None

    if usernewsitem is None:
        usernewsitem = UserNewsItem()
        usernewsitem.user = user
        usernewsitem.title = feed_items[ns.item].title
        usernewsitem.summary = feed_items[ns.item].summary
        usernewsitem.link = link
        usernewsitem.published = news_published
        usernewsitem.news_site = NewsSite.objects\
            .get(news_site=ns.current_news_site)
        usernewsitem.save()

        logger.info(f'user {user.username}, storing news from '\
                    f'{usernewsitem.news_site} with topic '\
                    f'{usernewsitem.title[:15]}..., ip: {ip}')


def add_width_to_img_tag(summary):
    ''' to fit images on the screen they need a maximum width of 100%
        there look for all img tags in the summary and insert width in the
        style
    '''

    # TODO check if there is already a width in the style
    # and to check actual size of the picture
    '''
    from PIL import Image
    import requests

    url = 'https://a.thumbs.redditmedia.com/dt7igrh2wPL59urJlkoiNrSkyhKXEX4AfI13LfPxva8.jpg'

    url = 'https://a.espncdn.com/photo/2019/0915/r598368_1296x729_16-9.jpg'

    im = Image.open(requests.get(url, stream=True).raw)

    width, height = im.size

    print(f'width: {width}, height: {height}')
')
    '''

    new_summary = summary
    for img_tag_match in re.finditer(r'<img.*?>', summary):
        img_tag = img_tag_match.group(0)

        if re.search(r'jpg&', img_tag):
            continue

        if re.search(r'<img.*style="', img_tag):
            new_img_tag = re.sub(r'style="', f'style="width: {IMG_WIDTH}; ', img_tag)

        else:
            new_img_tag = re.sub(r'<img ', f'<img style="width: {IMG_WIDTH}" ', img_tag)

        new_summary = re.sub(img_tag, new_img_tag, new_summary)

    return new_summary


def create_news_context(ns, news_sites, feed_items):
    ''' create news context to be rendered to newspage
        arguments:
        :ns: news status (type recordtype)
        :feed_items: feed items (feedparser dict type)
        return:
        :context: dict with newspage items
    '''
    DELAY_FACTOR = 35
    MIN_CHARS = 350
    BANNER_LENGTH = 150
    HELP_ARROWS = 'Use left/ right arrow to toggle news items. '
    HELP_BANNER = 'Press Banner to toggle banner on/ off. '

    news_published = feedparser_time_to_datetime(feed_items[ns.item])

    reference_text = ''.join([
        NewsSite.objects.get(news_site=ns.current_news_site).news_url,
        ', updated: ',
        news_published.strftime('%a, %d %B %Y %H:%M:%S GMT')
    ])
    status_text = ''.join([
        'News item: ', str(ns.item+1), ' from ', str(ns.news_items)])

    news_title = feed_items[ns.item].title
    news_link = feed_items[ns.item].link
    news_summary = feed_items[ns.item].summary
    news_summary = add_width_to_img_tag(news_summary)
    news_summary = remove_feedburner_reference(news_summary)
    news_summary_flat_text = remove_all_references(news_summary)

    pprint(news_summary)

    if news_summary == news_title:
        news_summary = ''
        news_summary_flat_text = ''

    length_summary = len(news_summary_flat_text)
    delay = max(MIN_CHARS, (len(news_title)+length_summary))*DELAY_FACTOR/1000
    if length_summary > BANNER_LENGTH:
        show_banner_button = False
        help_banner = ''
    else:
        show_banner_button = True
        help_banner = HELP_BANNER

    context = {'news_sites': news_sites,
               'news_site': ns.current_news_site,
               'reference': reference_text,
               'status': status_text,
               'news_link': news_link,
               'news_title': news_title,
               'news_summary': news_summary,
               'news_summary_flat_text': news_summary_flat_text,
               'delay': delay,
               'show_banner_button': show_banner_button,
               'banner': ns.banner,
               'help_arrows': HELP_ARROWS,
               'help_banner': help_banner,
               'error_message': ns.error_message,
              }

    return context


def obtain_news_sites_and_news_status_for_user(request, user):
    try:
        default_news_sites = [item.news_site for item in UserNewsSite.objects.get(
            user__username='default_user').news_sites.all()]

    except (ObjectDoesNotExist, TypeError):
        default_news_sites = []

    try:
        news_sites = [item.news_site for item in UserNewsSite.objects.get(
            user=user).news_sites.all()]

    except (ObjectDoesNotExist, TypeError):
        news_sites = default_news_sites

    if news_sites == []:
        # empty newssites to result in a redirect to newssites to select a
        # newssite.
        ns = None
    else:
        try:
            ns = get_session_newsstatus(request)

            # check if current news site is not deleted. If it is then select
            # the default site
            if ns.current_news_site not in [
                    site.news_site for site in NewsSite.objects.all()]:
                try:
                    ns.current_news_site = default_news_sites[0]

                except KeyError:
                    ns.current_news_site = ''

        except (KeyError, AttributeError):
            ns = NewsStatus(current_news_site=news_sites[0],
                            news_site='',
                            updated='',
                            item=0,
                            news_items=0,
                            banner=False,
                            error_message='')

    news_sites.sort()
    return news_sites, ns
