from django import forms
from .widgets import FengyuanChenDatePickerInput
from stock.models import Person
from howdimain.howdimain_vars import BASE_CURRENCIES, STOCK_DETAILS
from .models import Exchange


class StockQuoteForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super(StockQuoteForm, self).__init__(*args, **kwargs)


        self.fields["quote_string"] = forms.CharField(
            max_length=150,
            widget=forms.TextInput(attrs={"size": "40%"}),
            required=False,
        )

        self.fields["selected_portfolio"] = forms.CharField(required=False)

        try:
            default_user = Person.objects.get(username="default_user")

        except Person.DoesNotExist:
            default_user = None

        portfolio_choices = default_user.get_portfolio_names() if default_user else []
        if user and user.is_authenticated:
            portfolio_choices += user.get_portfolio_names()
        self.fields["portfolios"] = forms.ChoiceField(
            widget=forms.Select(),
            choices=[(p, p) for p in portfolio_choices],
            required=False,
        )

        exchange_choices = [
            (exchange.mic, exchange.name)
            for exchange in Exchange.objects.all().order_by("name")
        ]
        self.fields["markets"] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
            choices=exchange_choices,
            required=True,
            label="",
        )

        self.fields["stockdetails"] = forms.ChoiceField(
            widget=forms.Select(),
            choices=STOCK_DETAILS,
            required=True,
        )

        self.fields["datepicked"] = forms.DateField(
            input_formats=["%d/%m/%Y"],
            widget=FengyuanChenDatePickerInput(
                attrs={"size": "9", "class": "btn btn-outline-primary btn-sm ms-1 mt-1"}
            ),
            required=True,
        )

        self.fields["date_is_today"] = forms.BooleanField(required=False)


class PortfolioForm(forms.Form):

    def __init__(self, *args, user=None, **kwargs):
        super(PortfolioForm, self).__init__(*args, **kwargs)

        self.fields["portfolio_name"] = forms.CharField(
            max_length=20,
            widget=forms.TextInput(attrs={"size": "10vw"}),
            required=False,
        )
        self.fields["new_portfolio"] = forms.CharField(required=False)
        self.fields["symbol"] = forms.CharField(
            max_length=10,
            widget=forms.TextInput(attrs={"size": "10vw"}),
            required=False,
        )
        self.fields["btn1_pressed"] = forms.CharField(required=False)
        self.fields["change_qty_btn_pressed"] = forms.CharField(required=False)
        self.fields["delete_symbol_btn_pressed"] = forms.CharField(required=False)

        portfolio_choices = (
            user.get_portfolio_names() if user and user.is_authenticated else []
        )
        self.fields["portfolios"] = forms.ChoiceField(
            widget=forms.Select(),
            choices=[(p, p) for p in portfolio_choices],
            required=False,
        )
        self.fields["currencies"] = forms.ChoiceField(
            widget=forms.Select(),
            choices=BASE_CURRENCIES,
            required=True,
        )
        self.fields["stockdetails"] = forms.ChoiceField(
            widget=forms.Select(),
            choices=STOCK_DETAILS,
            required=True,
        )
        self.fields["datepicked"] = forms.DateField(
            input_formats=["%d/%m/%Y"],
            widget=FengyuanChenDatePickerInput(
                attrs={"size": "9", "class": "btn btn-outline-primary btn-sm ms-1 mt-1"}
            ),
            required=False,
        )
        self.fields["date_is_today"] = forms.BooleanField(required=False)
