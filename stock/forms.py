from django import forms
from .models import Exchange

class StockQuoteForm(forms.ModelForm):
    quote_string = forms.CharField(max_length=50,
        widget=forms.TextInput(attrs={'size':'40%'}))

    markets = forms.ModelMultipleChoiceField(
                widget=forms.CheckboxSelectMultiple(),
                required=False,
                label='',
                queryset=Exchange.objects.all().order_by('exchange_long')
    )

    class Meta:
        model = Exchange
        fields = ['quote_string', 'markets']
