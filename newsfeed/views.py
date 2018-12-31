from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from .module_news import update_news
from .models import NewsSite, UserNewsSite
from .forms import SelectedSitesForm
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from pprint import pprint
from utils.plogger import Logger
import time
import re


logformat = '%(asctime)s:%(levelname)s:%(message)s'
Logger.set_logger('logs/howdimain.log', logformat, 'INFO')


class NewsFeed:
    '''  NewsFeed class with view methods:
         - newspage
         - newssites
    '''
    DELAY_FACTOR = 35
    MIN_CHARS = 350
    BANNER_LENGTH = 150
    HELP_ARROWS = 'You can use left/ right arrow to toggle news items. '
    HELP_BANNER = 'Press Banner to toggle banner on/ off. '


    @classmethod
    def newspage(cls, request):
        logger = Logger.getlogger()

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
        except (KeyError, AttributeError):
            current_news_site = newssites[0]
            news_site = ''
            item = 0
            news_items = 0
            banner = False

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
        logger.info(f'update: {update_news_true}')
        if update_news_true:
            feed_items = update_news(NewsSite.objects.get(
                   news_site=current_news_site).news_url)
            logger.info(f'{feed_items}')
            request.session['feed'] = feed_items
            news_site = current_news_site
            item = 0
        else:
            feed_items = request.session['feed']

        news_items = len(feed_items)
        if news_items == 0:
            home_url = reverse('home')
            return redirect(home_url)

        reference_text = ''.join(['News update from ', NewsSite.objects.get(
                                 news_site=current_news_site).news_url,
                                 ' on ', time.ctime()])
        status_text = ''.join(['News item: ', str(item+1), ' from ',
                              str(news_items)])
        news_title = feed_items[item]["title"]
        news_summary = feed_items[item]["summary"]
        news_summary_flat_text = re.sub(r'<.*?>', '', news_summary)
        length_summary = len(news_summary)
        delay = max(cls.MIN_CHARS, (len(news_title)+length_summary))*cls.DELAY_FACTOR/1000
        if length_summary > cls.BANNER_LENGTH:
            show_banner_button = False
            help_banner = ''
        else:
            show_banner_button = True
            help_banner = cls.HELP_BANNER

        request.session['news_site'] = news_site
        request.session['current_news_site'] = current_news_site
        request.session['item'] = item
        request.session['news_items'] = news_items
        request.session['banner'] = banner

        context = {'newssites': newssites,
                   'news_site': current_news_site,
                   'reference': reference_text,
                   'status': status_text,
                   'news_title': news_title,
                   'news_summary': news_summary,
                   'news_summary_flat_text': news_summary_flat_text,
                   'delay': delay,
                   'show_banner_button': show_banner_button,
                   'banner': banner,
                   'help_arrows': cls.HELP_ARROWS,
                   'help_banner': help_banner,
                  }

        return render(request, 'newspage.html', context)

    @classmethod
    def newssites(cls, request):

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

                UserNewsSite.objects.filter(user=user).delete()
                try:
                    usersites = UserNewsSite(user=user)
                    usersites.save()
                except IntegrityError:
                    usersites = UserNewsSite.objects.get(user=user)

                for site in selected_sites:
                    newssite = NewsSite.objects.get(news_site=site)
                    usersites.news_sites.add(newssite)
                    usersites.save()

                newsfeed_url = reverse('newspage')
                return redirect(newsfeed_url)
        else:
            form = SelectedSitesForm()
            form.fields['selected_sites'].initial = choices

        return render(request, 'newssites.html', {'form':form})
