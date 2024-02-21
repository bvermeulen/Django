from django.core.validators import RegexValidator
from django import forms
from captcha.fields import CaptchaField
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

no_special_character = RegexValidator(r'^[^/#*&?(){}$%^+=<>:;|!@"*\^\'[\]\\]*$')

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput())
    first_name = forms.CharField(max_length=30, validators=[no_special_character], required=True)
    last_name = forms.CharField(max_length=30, validators=[no_special_character], required=False)
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'first_name', 'last_name')


class UserUpdateForm(forms.ModelForm):
    email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())
    first_name = forms.CharField(max_length=30, validators=[no_special_character], required=False)
    last_name = forms.CharField(max_length=30, validators=[no_special_character], required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
