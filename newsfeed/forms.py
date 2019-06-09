from django import forms
from .models import NewsSite

class SelectedSitesForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SelectedSitesForm, self).__init__(*args, **kwargs)

        newssite_choices = []
        for site in NewsSite.objects.all():
            newssite_choices.append((site, site))

        newssite_choices.sort(key=lambda site: site[0].news_site)

        self.fields['selected_sites'] = forms.MultipleChoiceField(
                            choices=newssite_choices,
                            widget=forms.CheckboxSelectMultiple(),
                            )
