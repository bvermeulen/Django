import re
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
        url = reverse("signup")
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve("/signup/")
        self.assertEqual(view.func, signup)

    def test_csrf(self):
        self.assertContains(self.response, "csrfmiddlewaretoken")

    def test_contains_form(self):
        form = self.response.context.get("form")
        self.assertIsInstance(form, SignUpForm)

    def test_form_inputs(self):
        """
        The view must contain seven inputs: csrf, username, email,
        password1, password2, first_name, last_name, captcha
        """
        self.assertContains(self.response, "<input", 9)
        self.assertContains(self.response, 'type="text"', 4)
        self.assertContains(self.response, 'type="email"', 1)
        self.assertContains(self.response, 'type="password"', 2)


class SuccessfulSignUpTests(TestCase):
    def setUp(self):
        url = reverse("signup")
        data = {
            "username": "johndean",
            "email": "johndean@hotmail.com",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
            "first_name": "john",
            "last_name": "dean",
            "captcha_0": "dummy_value",
            "captcha_1": "PASSED",
        }
        self.response = self.client.post(url, data)
        self.email_verification = mail.outbox[0]
        self.email_welcome = mail.outbox[1]
        self.home_url = reverse("home")

        _ = Home.objects.create(
            welcome_text="hello stranger",
            welcome_image="image.jpg",
            member_text="hello member",
            member_image="image.jpg",
        )

    def test_redirection(self):
        """
        A valid form submission should redirect the user to the home page
        """
        self.assertRedirects(self.response, self.home_url)

    def test_user_creation(self):
        self.assertTrue(User.objects.exists())

    def test_user_is_not_active(self):
        """
        User is created and has status not active
        """
        self.assertFalse(User.objects.all()[0].is_active)

    def test_send_verification_email(self):
        """test if verification email has been send"""
        self.assertEqual(["johndean@hotmail.com"], self.email_verification.to)
        self.assertEqual(
            "Howdimain verification email", self.email_verification.subject
        )
        self.assertIn("info@howdiweb.nl", self.email_verification.body)
        self.assertIn("This email is machine generated", self.email_verification.body)

    def test_verification_valid_token(self):
        html_text = self.email_verification.alternatives[0][0]
        regex = r'verify-email\/(.*?)\/(.*?)/'
        m = re.search(regex, html_text)
        email_token = m.group(1)
        token = m.group(2)
        url = reverse("verify-email", args=(email_token, token))
        response = self.client.post(url)
        self.assertContains(response, 'verified successfully')
        self.assertTrue(User.objects.all()[0].is_active)

    def test_verification_invalid_token(self):
        html_text = self.email_verification.alternatives[0][0]
        regex = r"verify-email\/(.*?)\/(.*?)/"
        m = re.search(regex, html_text)
        email_token = m.group(1)
        token = 'false_token'
        url = reverse("verify-email", args=(email_token, token))
        response = self.client.post(url)
        self.assertNotContains(response, "verified successfully")
        self.assertFalse(User.objects.all()[0].is_active)

    def test_send_welcome_mail(self):
        """test if welcome email has been send"""
        self.assertEqual(
            ["johndean@hotmail.com", "admin@howdiweb.nl"], self.email_welcome.to
        )
        self.assertEqual("[Howdiweb] Welcome message", self.email_welcome.subject)
        self.assertIn("john", self.email_welcome.body)
        self.assertIn("johndean", self.email_welcome.body)


class InvalidSignUpTests(TestCase):
    def setUp(self):
        url = reverse("signup")
        self.response = self.client.post(url, {})  # submit an empty dictionary

    def test_signup_status_code(self):
        """
        An invalid form submission should return to the same page
        """
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get("form")
        self.assertTrue(form.errors)

    def test_dont_create_user(self):
        self.assertFalse(User.objects.exists())

    def test_user_already_exists(self):
        """
        A submission with a user with same email should return to the same page
        """
        _ = User.objects.create(username="joebiden", email="johndean@hotmail.com")
        url = reverse("signup")
        data = {
            "username": "johndean",
            "email": "johndean@hotmail.com",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
            "first_name": "john",
            "last_name": "dean",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
