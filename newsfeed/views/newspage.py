import datetime
from collections import namedtuple
from django.shortcuts import render, redirect, reverse
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from howdimain.howdimain_vars import LEFT_ARROW, RIGHT_ARROW
from ..module_news import update_news, restore_feedparserdict
from ..models import NewsSite, UserNewsSite
from .views_utils import (set_session_newsstatus,
                          store_news_item, create_news_context,
                          obtain_news_sites_and_news_status_for_user,
                         )


logger = Logger.getlogger()
Controls = namedtuple('Controls', 'banner store next previous')

# these controls determine what is shown on the template buttons and links
cntr = Controls('Banner', 'store this news item',
                RIGHT_ARROW, LEFT_ARROW)

def newspage(request):
    ''' views function to render newspage.html
    '''
    user = request.user
    news_sites, ns = obtain_news_sites_and_news_status_for_user(request, user)
    if news_sites == []:
        return redirect(reverse('newssites'))

    button_cntr = request.POST.get('control_btn')
    button_site = request.POST.get('site_btn')
    if not button_cntr or button_cntr == cntr.next:
        ns.item += 1
    elif button_cntr == cntr.previous:
        ns.item -= 1
    elif button_cntr == cntr.banner:
        ns.banner = not ns.banner
    elif button_cntr == cntr.store:
        pass
    else:
        logger.warn(f'ValueError {button_cntr}: check template')

    if ns.news_items != 0:
        ns.item = ns.item % ns.news_items
    else:
        ns.item = 0

    if button_site:
        ns.current_news_site = button_site

    today = datetime.date.today().strftime("%d-%m-%Y")
    update_news_true = (ns.current_news_site != ns.news_site) or \
                       (ns.item == 0 and not button_cntr) or \
                       (ns.updated != today)
    if update_news_true:
        feed_items = update_news(NewsSite.objects.get(
            news_site=ns.current_news_site).news_url)
        request.session['feed'] = feed_items
        ns.news_site = ns.current_news_site
        ns.updated = today
        ns.item = 0
        ns.banner = False

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
    if button_cntr == cntr.store and user.is_authenticated:
        store_news_item(user, ns, feed_items, ip_address)

    context = create_news_context(ns, news_sites, feed_items)

    # store status session for next time newsfeed is called and remove
    # the error message
    ns.error_message = ''
    set_session_newsstatus(request, ns)

    context['controls'] = cntr

    logger.info(f'user {user}, browsing news: {ns.current_news_site}, ip: {ip_address}')
    return render(request, 'newsfeed/newspage.html', context)
