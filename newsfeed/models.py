from django.db import models
from django.contrib.auth.models import User


class NewsSite(models.Model):
    news_site = models.CharField(max_length=15, unique=True)
    news_url = models.URLField()

    def __str__(self):
        return self.news_site


class UserNewsSite(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    news_sites = models.ManyToManyField(NewsSite)

    def __unicode__(self):
        return User.objects.get(username=self.user).news_sites
