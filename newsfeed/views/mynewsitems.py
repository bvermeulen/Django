from typing import Any
import math
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from howdimain.howdimain_vars import ITEMS_PER_PAGE
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from .views_utils import NewsStatus, set_session_newsstatus
from ..models import UserNewsItem


logger = Logger.getlogger()


@method_decorator(login_required, name="dispatch")
class MyNewsItems(ListView):
    model = UserNewsItem
    context_object_name = "newsitems"
    template_name = "newsfeed/mynewsitems.html"
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[Any]:
        news_items = UserNewsItem.objects.filter(user=self.request.user).order_by(
            "-published"
        )
        return news_items

    def post(self, request):
        deleted_item_pk = request.POST.get("deleted_item_pk")
        if deleted_item_pk:
            page, item = self.get_page_number(deleted_item_pk)
            get_object_or_404(UserNewsItem, pk=deleted_item_pk).delete()
            page  = min(page, math.ceil(len(self.get_queryset())/ ITEMS_PER_PAGE))
            self.log_deletion(item)
            mynews_url = reverse("mynewsitems")
            if page <= 1:
                return redirect(mynews_url)
            else:
                url = f"{mynews_url}?page={page}"
                return redirect(url)

        button_site = request.POST.get("site_btn")
        if button_site:
            ns = NewsStatus(
                current_news_site=button_site,
                item=0,
                news_site="",
                updated="",
                news_items=0,
                banner=0,
                scroll=0,
                error_message="",
            )
            set_session_newsstatus(request, ns)
            return redirect(reverse("newspage"))

    def get_page_number(self, item_pk):
        for i, item in enumerate(self.get_queryset(), start=1):
            if item.pk == int(item_pk):
                return math.ceil(i / ITEMS_PER_PAGE), item
        return 1, None

    def log_deletion(self, item):
        if item is None:
            return

        ip_address = get_client_ip(self.request)
        logger.info(
            f"user {self.request.user} ({ip_address}) deleted: {item}"
        )
