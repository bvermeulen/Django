from django import forms

class StockQuoteForm(forms.Form):
    quote_string = forms.CharField(max_length=50,
        widget=forms.TextInput(attrs={'size':'40%'}))
