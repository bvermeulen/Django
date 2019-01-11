from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.test import TestCase
from ..views import newspage, newssites
from ..models import NewsSite, UserNewsSite
from django.contrib.auth import login


class NewsPageTests(TestCase):
    def setUp(self):
        self.newssite = NewsSite.objects.create(news_site='Django_News', news_url='django_news.com')
        self.user = User.objects.create(username='default_user')
        self.usernewssite = UserNewsSite.objects.create(user=self.user)
        self.usernewssite.news_sites.add(self.newssite)
        url = reverse('newspage')
        self.response = self.client.get(url, follow=True)

    def test_newspage_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_newspage_url_resolves_newspage_view(self):
        view = resolve('/news/')
        self.assertEquals(view.func, newspage)

    def test_newspag_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, 'href="{0}"'.format(home_url))


class NewsSitesTests(TestCase):
    def setUp(self):
        self.newssite = NewsSite.objects.create(news_site='Django_News', news_url='django_news.com')
        self.default_user = User.objects.create(username='default_user')
        self.usernewssite = UserNewsSite.objects.create(user=self.default_user)
        self.usernewssite.news_sites.add(self.newssite)
        self.temp_user = User.objects.create(username='testuser', email='testuser@mail.com', password='123')
        self.client.login(username='testuser', password='123')

        url = reverse('newssites')
        self.response = self.client.get(url, follow=True)

    def test_newssites_url_resolves_newspage_view(self):
        view = resolve('/news/sites/')
        self.assertEquals(view.func, newssites)

    def test_newssites_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_newssites_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, 'href="{0}"'.format(home_url))
