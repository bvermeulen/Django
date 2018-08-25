from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=100)

    def get_post_count(self):
        return sum(self.topics.get(id=i).posts.all().count() \
                   for i in range(1, self.topics.count()+1))


    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE,
                              related_name='topics')
    starter = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='topics')

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

    def __str__(self):
        return self.message
