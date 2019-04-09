from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator
from django.utils.html import mark_safe
from django import template
import math
from markdown import markdown
from utils.mdx_del_ins import DelInsExtension

register = template.Library()

class Board(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=100)

    def get_posts_count(self):
        return Post.objects.filter(topic__board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE,
                              related_name='topics')
    starter = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='topics')
    views = models.PositiveIntegerField(default=0)

    posts_per_page = 2

    def get_page_count(self):
        count = self.posts.count()
        pages = count / self.posts_per_page
        if pages == 0:
            pages += 1
        return math.ceil(pages)

    def has_many_pages(self, count=None):
        if count is None:
            count = self.get_page_count()
        return count > 3

    def get_page_range(self):
        count = self.get_page_count()
        if self.has_many_pages():
            return range(1,4)
        else:
            return range(1, count+1)

    def get_page_number(self, post_pk):
        for i, post in enumerate(self.posts.all()):
            if post.pk == post_pk:
                return int(i/self.posts_per_page)+1

        return 1

    def __str__(self):
        return self.subject


class Post(models.Model):
    message = models.TextField(max_length=4000)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,
                              related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='posts')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, related_name='+')

    def get_message_as_markdown(self):
        markdown_text = mark_safe(markdown(self.message,
                    extensions=['tables', 'fenced_code', DelInsExtension()],
                    safe_mode='escape'))
        return markdown_text

    def __str__(self):
            truncated_message = Truncator(self.message)
            return truncated_message.chars(30)
