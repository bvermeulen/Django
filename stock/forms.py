from django import forms
from howdimain.howdimain_vars import BASE_CURRENCIES, STOCK_DETAILS
from .models import Exchange

class StockQuoteForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(StockQuoteForm, self).__init__(*args, **kwargs)

        self.fields['quote_string'] = forms.CharField(
            max_length=150,
            widget=forms.TextInput(attrs={'size':'40%'}), required=False)

        self.fields['selected_portfolio'] = forms.CharField(required=False)

        choices = [(exchange.mic, exchange.name)
                   for exchange in Exchange.objects.all().order_by('name')]

        self.fields['markets'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
            choices=choices,
            required=False,
            label='',
        )


class PortfolioForm(forms.Form):

    def __init__(self, *args, user=None, **kwargs):
        super(PortfolioForm, self).__init__(*args, **kwargs)

        self.fields['portfolio_name'] = forms.CharField(
            max_length=20, widget=forms.TextInput(attrs={'size':'10vw'}),
            required=False)
        self.fields['new_portfolio'] = forms.CharField(required=False)
        self.fields['symbol'] = forms.CharField(
            max_length=10, widget=forms.TextInput(attrs={'size':'10vw'}),
            required=False)
        self.fields['btn1_pressed'] = forms.CharField(required=False)
        self.fields['change_qty_btn_pressed'] = forms.CharField(required=False)
        self.fields['delete_symbol_btn_pressed'] = forms.CharField(required=False)
        self.fields['exchangerate'] = forms.CharField(required=False)

        self.fields['portfolios'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=list(zip(user.get_portfolio_names(), user.get_portfolio_names())),
            required=False,
        )
        self.fields['currencies'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=BASE_CURRENCIES,
            required=True,
        )
        self.fields['stockdetails'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=STOCK_DETAILS,
            required=True,
        )
