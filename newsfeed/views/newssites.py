from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from ..module_news import update_news
from ..models import NewsSite, UserNewsSite
from ..forms import SelectedSitesForm, NewSiteForm
from howdimain.utils.plogger import Logger


logger = Logger.getlogger()


@login_required
def newssites(request):
    ''' views function to render newssites.html
    '''
    new_site_error_message = ''
    choices = []
    user = request.user
    try:
        for site in UserNewsSite.objects.get(user=user).news_sites.all():
            choices.append(site.news_site)
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':

        form_select_sites = SelectedSitesForm(request.POST)
        form_new_site = NewSiteForm(request.POST)
        if form_select_sites.is_valid() and not form_new_site.is_valid():
            selected_sites = form_select_sites.cleaned_data.get('selected_sites')
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
            return redirect(reverse('newspage'))

        else:
            # new site is selected, so set select_sites to initial choices
            form_select_sites = SelectedSitesForm()
            form_select_sites.initial['selected_sites'] = choices

        if form_new_site.is_valid():
            test_feed = update_news(form_new_site.cleaned_data.get('news_url'))
            if test_feed:
                form_new_site.save()
                form_new_site = NewSiteForm()
                form_new_site.initial['news_site'] = 'site name'
                form_new_site.initial['news_url'] = 'url'

            else:
                new_site_error_message = \
                    f'Site {form_new_site.cleaned_data.get("news_site")} did not '\
                    f'return a valid RSS'

            # update to include the new news site
            form_select_sites = SelectedSitesForm()
            form_select_sites.initial['selected_sites'] = choices

        else:
            # error handling: if news_site is valid then url is incorrect
            if form_new_site.cleaned_data.get('news_site'):
                new_site_error_message = \
                    f'URL {form_new_site.data.get("news_url")} is not properly formed'
            else:
                new_site_error_message = \
                    f'News site {form_new_site.data.get("news_site")} already exists'

            _site = form_new_site.data.get('news_site')
            _url = form_new_site.data.get('news_url')
            form_new_site = NewSiteForm()
            form_new_site.initial['news_site'] = _site
            form_new_site.initial['news_url'] = _url

    else:
        form_new_site = NewSiteForm()
        form_new_site.initial['news_site'] = 'site name'
        form_new_site.initial['news_url'] = 'url'
        form_select_sites = SelectedSitesForm()
        form_select_sites.initial['selected_sites'] = choices

    context = { 'form_select_sites': form_select_sites,
                'form_new_site': form_new_site,
                'new_site_error_message': new_site_error_message, }

    return render(request, 'newsfeed/newssites.html', context)
