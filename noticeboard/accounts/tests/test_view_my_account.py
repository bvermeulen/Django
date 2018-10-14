from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.urls import resolve
from django.test import TestCase
from ..views import UserUpdateView


class UpdateTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='john', email='john@doe.com', password='123')
        self.client.login(username='john', password='123')
        url = reverse('my_account')
        self.response = self.client.get(url)

    def test_my_account_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_my_account_url_resolves_signup_view(self):
        view = resolve('/settings/account/')
        self.assertEquals(view.func.view_class, UserUpdateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_inputs(self):
        '''
        The view must contain four inputs: csrf, first_name, last_name, email
        '''
        data = self.response.context.get('form')
        self.assertTrue('first_name' in data.fields)
        self.assertTrue('last_name' in data.fields)
        self.assertTrue('email' in data.fields)

class Successfull_My_AccountTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='john', email='john@doe.com', password='123')
        self.client.login(username='john', password='123')
        url = reverse('my_account')
        data = {
            'first_name': 'John',
            'last_name': 'Dear',
            'last_name': 'john@hotmail.com',
        }
        self.response = self.client.post(url, data)
        self.home_url = reverse('home')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''
        self.assertRedirects(self.response, self.home_url)