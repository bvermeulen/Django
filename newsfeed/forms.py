from django import forms
from .models import NewsSite

class SelectedSitesForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SelectedSitesForm, self).__init__(*args, **kwargs)

        newssite_choices = []
        for site in NewsSite.objects.all():
            print(site)
            newssite_choices.append((site, site))

        newssite_choices = tuple(newssite_choices)

        self.fields['selected_sites'] = forms.MultipleChoiceField(
                            choices=newssite_choices,
                            widget=forms.CheckboxSelectMultiple(),
                            )
