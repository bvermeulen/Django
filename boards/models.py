from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator
from django import template
from django.core.exceptions import ObjectDoesNotExist
from martor.models import MartorField
from martor.utils import markdownify
from .boards_settings import (MESSAGE_FIELD_SIZE, BOARD_NAME_SIZE,
                              DESCRIPTION_SIZE, TOPIC_SUBJECT_SIZE,
                              HAS_MANY_PAGES_LIMIT, POST_SUBJECT_SIZE,
                             )
import math


class AllowedUser(models.Model):
    primary_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                     related_name='+')
    allowed_user = models.ManyToManyField(User)

    def get_list_allowed_users(self):
        return self.allowed_user.all()

    def __str__(self):
        return self.primary_user.username


class Board(models.Model):
    name = models.CharField(max_length=BOARD_NAME_SIZE, unique=True)
    description = models.CharField(max_length=DESCRIPTION_SIZE)

    def get_posts_count(self):
        return Post.objects.filter(topic__board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()

    def __str__(self):
        return self.name


class Topic(models.Model):
    topic_subject = models.CharField(max_length=TOPIC_SUBJECT_SIZE)
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
        return count > HAS_MANY_PAGES_LIMIT

    def get_page_range(self):
        count = self.get_page_count()
        if self.has_many_pages():
            return range(1,HAS_MANY_PAGES_LIMIT+1)
        else:
            return range(1, count+1)

    def get_page_number(self, post_pk):
        for i, post in enumerate(self.posts.all().order_by('-updated_at')):
            if post.pk == post_pk:
                return int(i/self.posts_per_page)+1
        return 1

    def __str__(self):
        return Truncator(self.topic_subject).chars(30)


class Post(models.Model):
    post_subject = models.CharField(max_length=POST_SUBJECT_SIZE, null=True)
    message = MartorField(max_length=MESSAGE_FIELD_SIZE,
                          help_text=f'Maximum length is {MESSAGE_FIELD_SIZE} characters',
                          )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,
                              related_name='posts')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='+', null=True)
    updated_at = models.DateTimeField(null=True)
    allowed_editor = models.ManyToManyField(User, blank=True)

    def get_allowed_users(self):
        try:
            allowed_list = AllowedUser.objects.get(primary_user=self.created_by).get_list_allowed_users()
        except ObjectDoesNotExist:
            allowed_list = []
        return allowed_list


    def get_message_as_markdown(self):
        return self.message

    def __str__(self):
            return Truncator(self.post_subject).chars(30)
