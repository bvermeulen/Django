from django import forms
from .models import Exchange, Portfolio

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


class PortfolioForm(forms.Form):

    def __init__(self, *args, user=None, **kwargs):
        super(PortfolioForm, self).__init__(*args, **kwargs)

        self.fields['portfolio_name'] = forms.CharField(max_length = 20,
            widget=forms.TextInput(attrs={'size':'10vw'}), required=False)
        self.fields['new_portfolio'] = forms.CharField(required=False)
        self.fields['symbol'] = forms.CharField(max_length = 10,
            widget=forms.TextInput(attrs={'size':'10vw'}), required=False)
        self.fields['currency'] = forms.CharField(required=False)
        self.fields['btn1_pressed'] = forms.CharField(required=False)
        self.fields['btn2_pressed'] = forms.CharField(required=False)

        portfolios = [(item.portfolio_name, item.portfolio_name)
            for item in Portfolio.objects.
            filter(user=user).order_by('portfolio_name')]

        self.fields['portfolios'] = forms.ChoiceField(
                    widget=forms.RadioSelect(),
                    choices=portfolios,
                    required=False,
                    )
