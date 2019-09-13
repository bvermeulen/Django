from django.core import mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.urls import resolve
from django.test import TestCase
from ..views import signup
from ..forms import SignUpForm
from ..models import Home


class SignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/signup/')
        self.assertEqual(view.func, signup)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SignUpForm)

    def test_form_inputs(self):
        '''
        The view must contain seven inputs: csrf, username, email,
        password1, password2, first_name, last_name
        '''
        self.assertContains(self.response, '<input', 7)
        self.assertContains(self.response, 'type="text"', 3)
        self.assertContains(self.response, 'type="email"', 1)
        self.assertContains(self.response, 'type="password"', 2)


class SuccessfulSignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        data = {
            'username': 'johndean',
            'email': 'johndean@hotmail.com',
            'password1': 'abcdef123456',
            'password2': 'abcdef123456',
            'first_name': 'john',
            'last_name': 'dean'}
        self.response = self.client.post(url, data)
        self.email = mail.outbox[0]
        self.home_url = reverse('home')

        _ = Home.objects.create(welcome_text='hello stranger', welcome_image='image.jpg',
                                member_text='hello member', member_image='image.jpg')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''
        self.assertRedirects(self.response, self.home_url)

    def test_user_creation(self):
        self.assertTrue(User.objects.exists())

    def test_send_email(self):
        ''' test if email has been send '''
        self.assertEqual(['johndean@hotmail.com', 'admin@howdiweb.nl'], self.email.to)
        self.assertEqual('[Howdiweb] Welcome message', self.email.subject)
        self.assertIn('john', self.email.body)
        self.assertIn('johndean', self.email.body)

    def test_user_authentication(self):
        '''
        Create a new request to an arbitrary page.
        The resulting response should now have a `user` to its context,
        after a successful sign up.
        '''
        response = self.client.get(self.home_url)
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)


class InvalidSignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        self.response = self.client.post(url, {})  # submit an empty dictionary

    def test_signup_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_dont_create_user(self):
        self.assertFalse(User.objects.exists())

    def test_user_already_exists(self):
        '''
        A submission with a user with same email should return to the same page
        '''
        _ = User.objects.create(username='joebiden', email='johndean@hotmail.com')
        url = reverse('signup')
        data = {
            'username': 'johndean',
            'email': 'johndean@hotmail.com',
            'password1': 'abcdef123456',
            'password2': 'abcdef123456',
            'first_name': 'john',
            'last_name': 'dean',}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
