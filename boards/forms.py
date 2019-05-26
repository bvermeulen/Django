from django.contrib.auth.models import User
from django import forms
from django.db.models import ManyToManyField
from .models import Topic, Post
from martor.fields import MartorFormField
from .boards_settings import MESSAGE_FIELD_SIZE

class NewTopicForm(forms.ModelForm):

    class Meta:
        model = Topic
        fields = ['subject',]


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message', 'allowed_editor', ]
