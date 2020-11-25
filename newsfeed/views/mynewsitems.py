from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from .views_utils import NewsStatus, set_session_newsstatus
from ..models import UserNewsItem


logger = Logger.getlogger()

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
                        item=0,
                        news_site='',
                        updated='',
                        news_items=0,
                        banner=0,
                        scroll=0,
                        error_message='')
        set_session_newsstatus(request, ns)
        return redirect(reverse('newspage'))

    # order reversed by publishing date
    context = {'newsitems': UserNewsItem.objects.filter(user=request.user).
                            order_by('-published')}
    return render(request, 'newsfeed/mynewsitems.html', context)
