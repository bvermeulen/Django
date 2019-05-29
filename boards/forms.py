from django.contrib.auth.models import User
from django import forms
from django.db.models import ManyToManyField
from .models import Topic, Post
from martor.fields import MartorFormField
from .boards_settings import MESSAGE_FIELD_SIZE

nl = '\n'

class NewTopicForm(forms.ModelForm):

    class Meta:
        model = Topic
        fields = ['topic_subject',]
        labels = {'topic_subject': 'Topic'}


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['allowed_editor', 'post_subject', 'message']
        labels = {'post_subject': 'Post subject', 'allowed_editor': ''}
        help_texts = {'allowed_editor': 'Hold cntrl or shift key and use spacebar to select/unselect'}
