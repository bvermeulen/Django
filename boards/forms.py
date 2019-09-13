from django.contrib.auth.models import User
from django import forms
from howdimain.howdimain_vars import EXCLUDE_USERS
from .models import Topic, Post

class NewTopicForm(forms.ModelForm):

    class Meta:
        model = Topic
        fields = ['topic_subject',]
        labels = {'topic_subject': 'Topic'}


class PostForm(forms.ModelForm):
    allowed_editor = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='',
        help_text='Selection is not required',
        queryset=User.objects.all().exclude(
            username__in=EXCLUDE_USERS).order_by('username'))

    class Meta:
        model = Post
        fields = ['allowed_editor', 'post_subject', 'message']
        labels = {'post_subject': 'Post subject'}
