from pprint import pprint
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.newspage import newspage
from ..models import NewsSite, UserNewsSite

class NewsPageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        BBC = NewsSite.objects.create(
            news_site='BBC', news_url='http://feeds.bbci.co.uk/news/world/rss.xml')
        default_user = User.objects.create(username='default_user')
        default_newssites = UserNewsSite.objects.create(user=default_user)
        default_newssites.news_sites.add(BBC)

        CNN = NewsSite.objects.create(
            news_site='CNN', news_url='http://rss.cnn.com/rss/edition_world.rss')
        cls.testuser = 'testuser'
        cls.testuser_pw = '123'
        cls.testuser_object = User.objects.create_user(username=cls.testuser,
                                                       email='testuser@aa.com',
                                                       password=cls.testuser_pw)
        testuser_newssites = UserNewsSite.objects.create(user=cls.testuser_object)
        testuser_newssites.news_sites.add(CNN)
        testuser_newssites.news_sites.add(BBC)


class NewsPageView(NewsPageTests):

    def setUp(self):
        self.response = self.client.post(reverse('newspage'))

    def test_csrf_token(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_newspage_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_newspage_url_resolves_newspage_view(self):
        view = resolve('/news/')
        self.assertEqual(view.func, newspage)

    def test_newspage_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_newspage_view_banner(self):
        pass

    def test_newspage_view_next_previous_buttons(self):
        pass

    def test_newspage_view_has_no_link_to_select_site(self):
        pass

    def test_newspage_view_has_no_link_to_mysites(self):
        pass

    def test_newspage_returns_default_newssite(self):
        self.assertEqual('BBC', self.response.context['news_sites'][0])

class NewsPageViewUser(NewsPageTests):

    def setUp(self):
        self.client.login(username=self.testuser, password=self.testuser_pw)

    def test_newspage_view_contains_link_to_select_sites(self):
        pass

    def test_newspage_view_contains_link_to_mysites(self):
        pass

    def test_newspage_returns_user_newssite(self):
        response = self.client.post(reverse('newspage'))
        self.assertEqual('CNN', response.context['news_sites'][1])

    def test_newspage_site_button(self):
        pass

    def test_create_html(self):
        response = self.client.post(reverse('newspage'))
        file_name = 'newsfeed/tests/test_newspage.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(response.content.decode())
