from django.test import TestCase
from ..forms import SignUpForm

class SignUpFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpForm()
        expected = ['username', 'email', 'password1', 'password2',
                    'first_name', 'last_name', 'captcha']
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)
