from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from .module_news import update_news
from .models import NewsSite, UserNewsSite
from .forms import SelectedSitesForm
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from utils.plogger import Logger
import time
import re

logger = Logger.getlogger()
DELAY_FACTOR = 35
MIN_CHARS = 350
BANNER_LENGTH = 150
HELP_ARROWS = 'Use left/ right arrow to toggle news items. '
HELP_BANNER = 'Press Banner to toggle banner on/ off. '


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def newspage(request):
    user = request.user
    if user:
        try:
            newssites = [item.news_site for item in UserNewsSite.objects.get(
                         user=user).news_sites.all()]

        except (ObjectDoesNotExist, TypeError):
            newssites = [item.news_site for item in UserNewsSite.objects.get(
                         user__username='default_user').news_sites.all()]

    else:
        newssites = [item.news_site for item in UserNewsSite.objects.get(
                     user__username='default_user').news_sites.all()]

    if newssites == []:
        newssites_url = reverse('newssites')
        return redirect(newssites_url)

    try:
        news_site = request.session['news_site']
        current_news_site = request.session['current_news_site']
        item = request.session['item']
        news_items = request.session['news_items']
        banner = request.session['banner']
        error_message = request.session['error_message']
    except (KeyError, AttributeError):
        current_news_site = newssites[0]
        news_site = ''
        item = 0
        news_items = 0
        banner = False
        error_message = ''

    logger.info(f'{user} is browsing news at {get_client_ip(request)}')

    button_cntr = request.POST.get('control_btn')
    button_site = request.POST.get('site_btn')
    if not button_cntr or button_cntr == 'next':
        item += 1
    elif button_cntr == 'previous':
        item -= 1
    elif button_cntr == 'Banner':
        banner = not banner
    else:
        assert False, 'button value incorrect: check template'
    try:
        item = item % news_items
    except ZeroDivisionError:
        pass

    if button_site:
        current_news_site = button_site

    update_news_true = (current_news_site != news_site) or \
                  (item == 0 and not button_cntr)
    if update_news_true:
        feed_items = update_news(NewsSite.objects.get(
               news_site=current_news_site).news_url)
        request.session['feed'] = feed_items
        news_site = current_news_site
        item = 0
    else:
        feed_items = request.session['feed']

    news_items = len(feed_items)

    # test if newsfeed is not empty, if it is return to defauilt newssite
    # and reset session
    if news_items == 0:
        default_site = str(UserNewsSite.objects.get(
                           user__username='default_user').news_sites.first())
        error_message = f'Newssite {current_news_site} is not available, '\
                        f'revert to default site {default_site}'
        logger.info(f'{current_news_site} is not available, revert to default site')
        request.session['news_site'] = ''
        request.session['current_news_site'] = default_site
        request.session['item'] = 0
        request.session['news_items'] = 0
        request.session['banner'] = banner
        request.session['error_message'] = error_message
        return redirect(reverse('newspage'))

    try:
        news_published = feed_items[item]["published"]
    except KeyError:
        try:
            news_published = feed_items[item]["updated"]
        except KeyError:
            news_published = time.ctime()

    reference_text = ''.join(['News update from ', NewsSite.objects.get(
                               news_site=current_news_site).news_url,
                              ' on ', news_published])
    status_text = ''.join(['News item: ', str(item+1), ' from ',
                          str(news_items)])
    news_title = feed_items[item]["title"]
    news_link = feed_items[item]["link"]

    news_summary = feed_items[item]["summary"]
    news_summary_flat_text = re.sub(r'<.*?>', '', news_summary)
    if news_summary == news_title or news_summary_flat_text == '':
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

    # store status in session for next time newsfeed is called
    request.session['news_site'] = news_site
    request.session['current_news_site'] = current_news_site
    request.session['item'] = item
    request.session['news_items'] = news_items
    request.session['banner'] = banner
    request.session['error_message'] = ''

    context = {'newssites': newssites,
               'news_site': current_news_site,
               'reference': reference_text,
               'status': status_text,
               'news_link': news_link,
               'news_title': news_title,
               'news_summary': news_summary,
               'news_summary_flat_text': news_summary_flat_text,
               'delay': delay,
               'show_banner_button': show_banner_button,
               'banner': banner,
               'help_arrows': HELP_ARROWS,
               'help_banner': help_banner,
               'error_message': error_message,
              }

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
