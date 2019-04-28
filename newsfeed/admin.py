from django.contrib import admin
from .models import UserNewsSite, UserNewsItem, NewsSite

admin.site.register(UserNewsSite)
admin.site.register(UserNewsItem)
admin.site.register(NewsSite)
