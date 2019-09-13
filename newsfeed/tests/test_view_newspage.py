from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views import newspage, newssites
from ..models import NewsSite, UserNewsSite

class NewsPageTests(TestCase):
    def setUp(self):
        self.newssite = NewsSite.objects.create(
            news_site='Django_News', news_url='django_news.com')
        self.user = User.objects.create(username='default_user')
        self.usernewssite = UserNewsSite.objects.create(user=self.user)
        self.usernewssite.news_sites.add(self.newssite)
        url = reverse('newspage')
        self.response = self.client.get(url, follow=True)

    def test_newspage_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_newspage_url_resolves_newspage_view(self):
        view = resolve('/news/')
        self.assertEqual(view.func, newspage)

    def test_newspag_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, 'href="{0}"'.format(home_url))


class NewsSitesTests(TestCase):
    def setUp(self):
        newssite = NewsSite.objects.create(
            news_site='Django_News', news_url='django_news.com')
        test_user = User.objects.create_user(
            username='testuser', email='testuser@mail.com', password='123')
        test_usernewssite = UserNewsSite(user=test_user)
        test_usernewssite.save()
        test_usernewssite.news_sites.add(newssite)
        test_usernewssite.save()

    def test_newssites_url_resolves_newssites_view(self):
        view = resolve('/news/sites/')
        self.assertEqual(view.func, newssites)

    def test_newssites_view_status_code(self):
        url = reverse('newssites')
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_newssites_view_contains_link_to_home_page(self):
        url = reverse('newssites')
        response = self.client.post(url, {}, follow=True)
        home_url = reverse('home')
        self.assertContains(response, 'href="{0}"'.format(home_url))

    def test_newssites_view_valid_form_redirects_to_newspage(self):
        self.client.login(username='testuser', password='123')
        valid_input = {'selected_sites': ['Django_News']}
        url = reverse('newssites')
        response = self.client.post(url, valid_input)
        newspage_url = reverse('newspage')
        self.assertRedirects(response, newspage_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)
