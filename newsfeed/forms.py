from django import forms
from .models import NewsSite


class SelectedSitesForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SelectedSitesForm, self).__init__(*args, **kwargs)

        newssite_choices = [(site.pk, site.news_site)\
         for site in NewsSite.objects.all().order_by('news_site')]

        self.fields['selected_sites'] = forms.MultipleChoiceField(
            choices=newssite_choices,
            widget=forms.CheckboxSelectMultiple(),
        )


class NewSiteForm(forms.ModelForm):

    class Meta:
        model = NewsSite
        fields = ['news_site', 'news_url']
        widgets = {'news_site': forms.TextInput(attrs={'style': 'width:10%'}),
                   'news_url': forms.TextInput(attrs={'style': 'width:40%'}),
                  }
