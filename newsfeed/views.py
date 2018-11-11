from django.shortcuts import render, redirect
from .module_news import update_news
from .models import NewsSite
import time

class NewsFeed:
    '''  NewsFeed class with view methods:
         - newspage
    '''
    DEFAULT_NEWS_SITE = 'Nu.nl'
    DELAY_FACTOR = 35

    @classmethod
    def newspage(cls, request):
        ip_address = request.session.get('ip_address','')
        if not ip_address:
            ip_address = request.META.get('REMOTE_ADDR', '')
            request.session['ip_address'] = ip_address
            request.session['current_news_site'] = cls.DEFAULT_NEWS_SITE
            request.session['news_site'] = ''
            request.session['item'] = 0
            request.session['news_items'] = 0

        news_site = request.session['news_site']
        current_news_site = request.session['current_news_site']
        item = request.session['item']
        news_items = request.session['news_items']

        button_cntr = request.POST.get('control_btn')
        button_site = request.POST.get('site_btn')
        if not button_cntr or button_cntr == 'next':
            item += 1
        elif button_cntr == 'previous':
            item -= 1
        else:
            assert False, 'button value incorrect: check template'
        try:
            item = item % news_items
        except ZeroDivisionError:
            pass

        if button_site:
            current_news_site = button_site

        do_update_news = (current_news_site != news_site) or \
                         (item == 0) and not button_cntr
        if do_update_news:
            feed = update_news(current_news_site)
            request.session['feed'] = feed
            news_site = current_news_site
            item = 0
        else:
            feed = request.session['feed']

        news_items = len(feed["entries"])

        reference_text = ''.join(['News update from ', NewsSite.objects.get(
                                 news_site=current_news_site).news_url,
                                 ' on ', time.ctime()])
        status_text = ''.join(['News item: ', str(item+1), ' from ',
                              str(news_items)])
        news_title = feed["entries"][item]["title"]
        news_summary = feed["entries"][item]["summary"]
        delay = len(news_summary)*cls.DELAY_FACTOR

        request.session['news_site'] = news_site
        request.session['current_news_site'] = current_news_site
        request.session['item'] = item
        request.session['news_items'] = news_items

        newssites = [item.news_site for item in NewsSite.objects.all()]
        context = {'newssites': newssites,
                   'news_site': current_news_site,
                   'reference': reference_text,
                   'status': status_text,
                   'news_title': news_title,
                   'news_summary': news_summary,
                   'delay': delay,
                  }

        return render(request, 'newspage.html', context)
