from django.contrib.auth.models import User
from django import forms
from howdimain.howdimain_vars import EXCLUDE_USERS
from .models import Board, Topic, Post


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return (
            f"{obj.first_name} {obj.last_name} ({obj.username})"
        )


class BoardForm(forms.ModelForm):
    contributor = UserMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="",
        help_text="Selection is not required",
        queryset=User.objects.all()
        .exclude(username__in=EXCLUDE_USERS)
        .order_by("username"),
    )
    delete_btn = forms.CharField(required=False)
    board_selection = forms.CharField(required=False)
    new_board_name = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(BoardForm, self).__init__(*args, **kwargs)

        self.fields["name"].widget.attrs["style"] = "width:300px;"

    class Meta:
        model = Board
        fields = [
            "name",
            "description",
            "contributor",
            "delete_btn",
            "board_selection",
            "new_board_name",
        ]
        labels = {"name": "Board name"}


class TopicForm(forms.ModelForm):

    class Meta:
        model = Topic
        fields = ["topic_subject"]
        labels = {"topic_subject": "Topic"}


class PostForm(forms.ModelForm):
    allowed_editor = UserMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="",
        help_text="Selection is not required",
        queryset=User.objects.all()
        .exclude(username__in=EXCLUDE_USERS)
        .order_by("username"),
    )

    class Meta:
        model = Post
        fields = ["allowed_editor", "post_subject", "message"]
        labels = {"post_subject": "Post subject"}
