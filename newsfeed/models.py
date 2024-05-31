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

    def __str__(self):
        return self.user.username


class UserNewsItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news_site = models.ForeignKey(NewsSite, on_delete=models.CASCADE)
    title = models.TextField(max_length=400)
    summary = models.TextField(max_length=4000)
    link = models.URLField()
    published = models.DateTimeField(null=True)

    def __str__(self):
        return (
            f"{self.news_site}: {self.title}, {self.published} ({self.link}) "
            f"(username: {self.user.username})"
        )
