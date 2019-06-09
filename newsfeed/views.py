from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from .module_news import (update_news, feedparser_time_to_datetime,
                          remove_feedburner_reference, remove_all_references,
                          restore_feedparserdict)
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

NewsStatus = recordtype('NewsStatus',
             'current_news_site news_site item news_items banner error_message')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def set_session_newsstatus(request, newsstatus):
    for key, value in newsstatus._asdict().items():
        request.session[key] = value


def get_session_newsstatus(request):
    ns_keys = NewsStatus(*[None]*6)
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

    if usernewsitem == None:
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


def create_news_context(ns, news_sites, feed_items):
    ''' create news context to be rendered to newspage
        arguments:
        :ns: news status (type recordtype)
        :feed_items: feed items (feedparser dict type)
        return:
        :context: dict with newspage items
    '''
    news_published = feedparser_time_to_datetime(feed_items[ns.item])

    reference_text = ''.join([NewsSite.objects.get(
        news_site=ns.current_news_site).news_url,
        ', updated: ', news_published.strftime('%a, %d %B %Y %H:%M:%S GMT')])
    status_text = ''.join(['News item: ', str(ns.item+1), ' from ',
                  str(ns.news_items)])

    news_title = feed_items[ns.item].title
    news_link = feed_items[ns.item].link
    news_summary = feed_items[ns.item].summary
    news_summary = remove_feedburner_reference(news_summary)
    news_summary_flat_text = remove_all_references(news_summary)
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
    default_news_sites = [item.news_site for item in UserNewsSite.objects.get(
                  user__username='default_user').news_sites.all()]

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
                ns.current_news_site = default_news_sites[0]

        except (KeyError, AttributeError):
            ns = NewsStatus(current_news_site=news_sites[0],
                            news_site='',
                            item=0,
                            news_items=0,
                            banner=False,
                            error_message='')

    news_sites.sort()
    return news_sites, ns


def newspage(request):
    ''' views function to render newspage.html
    '''
    user = request.user
    news_sites, ns = obtain_news_sites_and_news_status_for_user(request, user)
    if news_sites == []:
        return redirect(reverse('newssites'))

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
        # restore feed items to FeedParserDict - for some reason Django sessions
        # converts them to Dict
        feed_items = restore_feedparserdict(feed_items)

    # test if newsfeed is not empty, if it is return to defauilt newssite
    # and reset session
    ns.news_items = len(feed_items)
    if ns.news_items == 0:
        default_site = str(UserNewsSite.objects.get(
                           user__username='default_user').news_sites.first())
        ns.error_message = f'Newssite {ns.current_news_site} is not available, '\
                           f'revert to default site {default_site}'
        logger.info(f'{ns.current_news_site} is not available, revert to default site')
        ns.current_news_site = default_site
        set_session_newsstatus(request, ns)
        return redirect(reverse('newspage'))

    # if button was pressed to store the news item then this is done here
    ip_address = get_client_ip(request)
    if button_cntr == cntr_store and user.is_authenticated:
        store_news_item(user, ns, feed_items, ip_address)

    context = create_news_context(ns, news_sites, feed_items)

    # store status session for next time newsfeed is called and remove
    # the error message
    ns.error_message = ''
    set_session_newsstatus(request, ns)

    logger.info(f'user {user}, browsing news: {ns.current_news_site}, ip: {ip_address}')
    return render(request, 'newsfeed/newspage.html', context)


@login_required
def mynewsitems(request):
    ''' views function to render mynewsitems.html
    '''
    ip_address = get_client_ip(request)
    logger.info(f'user {request.user}, watching personal newsitems, ip: {ip_address}')

    deleted_item_pk = request.POST.get('deleted_item_pk')
    if deleted_item_pk:
        get_object_or_404(UserNewsItem, pk=deleted_item_pk).delete()

    button_site = request.POST.get('site_btn')
    if button_site:
        ns = NewsStatus(current_news_site=button_site,
                        news_site='',
                        item=0,
                        news_items=0,
                        banner=False,
                        error_message='')
        set_session_newsstatus(request, ns)
        return redirect(reverse('newspage'))

    # order reversed by publishing date
    context = {'newsitems': UserNewsItem.objects.filter(user=request.user).
                            order_by('-published')}
    return render(request, 'newsfeed/mynewsitems.html', context)


@login_required
def newssites(request):
    ''' views function to render newssites.html
    '''
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
                logger.info(f'user {user.username}, made a new news selection')
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
