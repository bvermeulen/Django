from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.newspage import newspage
from ..models import NewsSite, UserNewsSite

class NewsPageTests(TestCase):
    def setUp(self):
        self.newssite = NewsSite.objects.create(
            news_site='BBC', news_url='http://feeds.bbci.co.uk/news/world/rss.xml')
        self.user = User.objects.create(username='default_user')
        self.usernewssite = UserNewsSite.objects.create(user=self.user)
        self.usernewssite.news_sites.add(self.newssite)
        self.response = self.client.get(reverse('newspage'), follow=True)

    def test_newspage_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_newspage_url_resolves_newspage_view(self):
        view = resolve('/news/')
        self.assertEqual(view.func, newspage)

    def test_newspage_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')
