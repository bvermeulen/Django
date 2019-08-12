from django import forms
from .models import Exchange

class StockQuoteForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(StockQuoteForm, self).__init__(*args, **kwargs)

        self.fields['quote_string'] = forms.CharField(max_length=150,
            widget=forms.TextInput(attrs={'size':'40%'}), required=False)

        self.fields['selected_portfolio'] = forms.CharField(required=False)

        choices = [(exchange.exchange_short, exchange.exchange_long)\
            for exchange in Exchange.objects.all().order_by('exchange_long')]

        self.fields['markets'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
            choices=choices,
            required=False,
            label='',
        )
