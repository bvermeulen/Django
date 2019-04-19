from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from .module_news import update_news, feedparser_time_to_datetime
from .models import NewsSite, UserNewsSite, UserNewsItem
from .forms import SelectedSitesForm
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
import re
from recordtype import recordtype

from utils.plogger import Logger

logger = Logger.getlogger()
DELAY_FACTOR = 35
MIN_CHARS = 350
BANNER_LENGTH = 150
HELP_ARROWS = 'Use left/ right arrow to toggle news items. '
HELP_BANNER = 'Press Banner to toggle banner on/ off. '

cntr_banner = 'Banner'
cntr_next = 'next'
cntr_previous = 'previous'
cntr_store = 'store this news item'

<<<<<<< HEAD
NewsStat = recordtype('NewsStat',
            'current_news_site news_site item news_items banner error_message')
=======
NewsStatus = recordtype('NewsStatus',
             'current_news_site news_site item news_items banner error_message')
>>>>>>> ea62716a7cbe26f8673db7a91270cfde237f27fc


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


<<<<<<< HEAD
def set_session_newsstatus(request, newsstat):
    for key, value in newsstat._asdict().items():
=======
def set_session_newsstatus(request, newsstatus):
    for key, value in newsstatus._asdict().items():
>>>>>>> ea62716a7cbe26f8673db7a91270cfde237f27fc
        request.session[key] = value


def get_session_newsstatus(request):
<<<<<<< HEAD
    ns_keys = NewsStat(*[None]*6)
    return NewsStat(*[request.session[key] for key, _ in ns_keys._asdict().items()])
=======
    ns_keys = NewsStatus(*[None]*6)
    return NewsStatus(*[request.session[key] for key, _ in ns_keys._asdict().items()])


def store_news_item(user, title, summary, link, published, site):
    logger.info(f'Store news by {user.username} of {title}')
    usernewsitem = UserNewsItem.objects.filter(user=user).filter(link=link).first()
    if usernewsitem and usernewsitem.published < published:
        usernewsitem.delete()
        usernewsitem = None

    if usernewsitem == None:
        usernewsitem = UserNewsItem()
        usernewsitem.user = user
        usernewsitem.title = title
        usernewsitem.summary = summary
        usernewsitem.link = link
        usernewsitem.published = published
        usernewsitem.save()
        usernewsitem.news_site.add(NewsSite.objects.get(news_site=site))
>>>>>>> ea62716a7cbe26f8673db7a91270cfde237f27fc


def newspage(request):
    user = request.user
    try:
        news_sites = [item.news_site for item in UserNewsSite.objects.get(
                      user=user).news_sites.all()]

    except (ObjectDoesNotExist, TypeError):
        news_sites = [item.news_site for item in UserNewsSite.objects.get(
                      user__username='default_user').news_sites.all()]

    if news_sites == []:
        return redirect(reverse('newssites'))

    try:
        ns = get_session_newsstatus(request)
    except (KeyError, AttributeError):
<<<<<<< HEAD
        ns = NewsStat(current_news_site=news_sites[0],
                      news_site='',
                      item=0,
                      news_items=0,
                      banner=False,
                      error_message='')
=======
        ns = NewsStatus(current_news_site=news_sites[0],
                        news_site='',
                        item=0,
                        news_items=0,
                        banner=False,
                        error_message='')
>>>>>>> ea62716a7cbe26f8673db7a91270cfde237f27fc

    logger.info(f'{user} is browsing news at {get_client_ip(request)}')

    button_cntr = request.POST.get('control_btn')
    button_site = request.POST.get('site_btn')
    if not button_cntr or button_cntr == cntr_next:
        ns.item += 1
    elif button_cntr == cntr_previous:
        ns.item -= 1
    elif button_cntr == cntr_banner:
        ns.banner = not ns.banner
    elif button_cntr == cntr_store:
        pass
    else:
        assert False, 'button value incorrect: check template'

    if ns.news_items != 0:
        ns.item = ns.item % ns.news_items
    else:
        ns.item = 0

    if button_site:
        ns.current_news_site = button_site

    update_news_true = (ns.current_news_site != ns.news_site) or \
                  (ns.item == 0 and not button_cntr)
    if update_news_true:
        feed_items = update_news(NewsSite.objects.get(
               news_site=ns.current_news_site).news_url)
        request.session['feed'] = feed_items
        ns.news_site = ns.current_news_site
        ns.item = 0
    else:
        feed_items = request.session['feed']

    ns.news_items = len(feed_items)

    # test if newsfeed is not empty, if it is return to defauilt newssite
    # and reset session
    if ns.news_items == 0:
        default_site = str(UserNewsSite.objects.get(
                           user__username='default_user').news_sites.first())
        ns.error_message = f'Newssite {ns.current_news_site} is not available, '\
                        f'revert to default site {default_site}'
        logger.info(f'{ns.current_news_site} is not available, revert to default site')
        ns.current_news_site = default_site
        set_session_newsstatus(request, ns)
        return redirect(reverse('newspage'))

    news_published = feedparser_time_to_datetime(feed_items[ns.item])

    reference_text = ''.join(['News update from ', NewsSite.objects.get(
        news_site=ns.current_news_site).news_url,
        ' on ', news_published.strftime('%a, %d %B %Y %H:%M:%S GMT')])
    status_text = ''.join(['News item: ', str(ns.item+1), ' from ',
        str(ns.news_items)])

    news_title = feed_items[ns.item]["title"]
    news_link = feed_items[ns.item]["link"]
    news_summary = feed_items[ns.item]["summary"]
    news_summary_flat_text = re.sub(r'<.*?>', '', news_summary)
    if news_summary == news_title or news_summary_flat_text == '':
        news_summary = ''
        news_summary_flat_text = ''

    # if button was entered to store the news item then this is done here
    if button_cntr == cntr_store and user.is_authenticated:
<<<<<<< HEAD
        logger.info(f'Annotate news by {user.username} of {news_title}')
        userannotated = UserAnnotatedNews()
        userannotated.user = user
        userannotated.title = news_title
        userannotated.summary = news_summary
        userannotated.link = news_link
        userannotated.published = news_published
        userannotated.save()
        userannotated.news_site.add(NewsSite.objects.get(news_site=ns.current_news_site))
=======
        store_news_item(user, news_title, news_summary, news_link,
                        news_published, ns.current_news_site)
>>>>>>> ea62716a7cbe26f8673db7a91270cfde237f27fc

    # render the newspage
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

    # store status session for next time newsfeed is called but remove the
    # error message
    ns.error_message = ''
    set_session_newsstatus(request, ns)

    return render(request, 'newsfeed/newspage.html', context)


@login_required
def newssites(request):

    choices = []
    user = request.user
    try:
        for site in UserNewsSite.objects.get(user=user).news_sites.all():
            choices.append(site.news_site)
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = SelectedSitesForm(request.POST)
        if form.is_valid():
            selected_sites = form.cleaned_data.get('selected_sites')

            # delete all entries for this user and then recreate with selection
            UserNewsSite.objects.filter(user=user).delete()
            try:
                usersites = UserNewsSite(user=user)
                usersites.save()
                logger.info(f'User {user.username} made a new news selection')
            except IntegrityError:
                logger.info('==> Check program this option is not possible')

            for site in selected_sites:
                newssite = NewsSite.objects.get(news_site=site)
                usersites.news_sites.add(newssite)

            usersites.save()
            newsfeed_url = reverse('newspage')
            return redirect(newsfeed_url)
        else:
            logger.info('==> form is not valid')
    else:
        form = SelectedSitesForm()
        form.fields['selected_sites'].initial = choices

    return render(request, 'newsfeed/newssites.html', {'form':form})
