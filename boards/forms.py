from django import forms
from .models import Topic, Post
from martor.fields import MartorFormField

class NewTopicForm(forms.ModelForm):
    message = MartorFormField(max_length=8000,
              help_text='Maximum length is 8000 characters',)

    class Meta:
        model = Topic
        fields = ['subject', 'message']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message', ]
