from django import forms
from .models import NewsSite

class SelectedSitesForm(forms.Form):

    newssite_choices = []
    for site in NewsSite.objects.all():
        newssite_choices.append((site, site))

    newssite_choices = tuple(newssite_choices)
    selected_sites = forms.MultipleChoiceField(choices=newssite_choices,
        widget=forms.CheckboxSelectMultiple())
