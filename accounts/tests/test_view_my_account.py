from django.contrib.auth.models import User
from django.urls import reverse
from django.urls import resolve
from django.test import TestCase
from ..views import UserUpdateView
from ..models import Home


class UpdateTests(TestCase):
    def setUp(self):
        _ = User.objects.create_user(username='john',
                                     email='john@doe.com', password='123')
        self.client.login(username='john', password='123')
        url = reverse('my_account')
        self.response = self.client.get(url)

    def test_my_account_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_my_account_url_resolves_signup_view(self):
        view = resolve('/settings/account/')
        self.assertEqual(view.func.view_class, UserUpdateView)

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
        _ = User.objects.create_user(username='john',
                                     email='john@doe.com', password='123')
        _ = Home.objects.create(welcome_text='hello stranger', welcome_image='image.jpg',
                                member_text='hello member', member_image='image.jpg')
        self.client.login(username='john', password='123')
        url = reverse('my_account')
        data = {
            'first_name': 'John',
            'last_name': 'Dear',
            'email': 'john@hotmail.com',
        }
        self.response = self.client.post(url, data)
        self.home_url = reverse('home')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''
        self.assertRedirects(self.response, self.home_url)
