from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from .module_news import update_news
from .models import NewsSite, UserNewsSite
from .forms import SelectedSitesForm
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
import time

class NewsFeed:
    '''  NewsFeed class with view methods:
         - newspage
    '''
    DELAY_FACTOR = 35

    @classmethod
    def newspage(cls, request):
        user = request.user
        ip_address = request.session.get('ip_address','')
        if user:
            try:
                newssites = [item.news_site for item in UserNewsSite.objects.get(
                                user=user).news_sites.all()]

            except Exception:
                newssites = [item.news_site for item in UserNewsSite.objects.get(
                             user__username='default_user').news_sites.all()]

        else:
            newssites = [item.news_site for item in UserNewsSite.objects.get(
                         user__username='default_user').news_sites.all()]

        if not ip_address:
            ip_address = request.META.get('REMOTE_ADDR', '')
            request.session['ip_address'] = ip_address
            request.session['current_news_site'] = newssites[0]
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
        if news_items == 0:
            home_url = reverse('home')
            return redirect(home_url)

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

        context = {'newssites': newssites,
                   'news_site': current_news_site,
                   'reference': reference_text,
                   'status': status_text,
                   'news_title': news_title,
                   'news_summary': news_summary,
                   'delay': delay,
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
