from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from howdimain.utils.html_utils import convert_string_to_html
from ..views.mynewsitems import MyNewsItems
from ..models import NewsSite, UserNewsSite, UserNewsItem
from ..module_news import update_news, feedparser_time_to_datetime

class MyNewsSitesViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='testuser',
                                 email='testuser@mail.com',
                                 password='123')

    def setUp(self):
        self.client.login(username='testuser', password='123')

    def test_newssites_url_resolves_mynewsitems_view(self):
        view = resolve('/news/mynewsitems/')
        self.assertEqual(view.func.view_class, MyNewsItems)

    def test_newssites_view_not_logged_in_redirects_to_login_page(self):
        self.client.logout()
        response = self.client.get(reverse('mynewsitems'))
        login_url = reverse('login') + f'?next={reverse("mynewsitems")}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

    def test_response_contains_csrf_token(self):
        response = self.client.get(reverse('mynewsitems'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_mynewsitems_view_contains_link_to_home_page(self):
        response = self.client.get(reverse('mynewsitems'))
        home_url = reverse('home')
        self.assertContains(response, f'href="{home_url}"')

    def test_mynewsitems_view_contains_link_to_newspage(self):
        response = self.client.get(reverse('mynewsitems'))
        news_url = reverse('newspage')
        self.assertContains(response, f'href="{news_url}"')


class MyNewsSitesPostTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.testuser = User.objects.create_user(username='testuser',
                                                email='testuser@mail.com',
                                                password='123')
        BBC = NewsSite.objects.create(
            news_site='BBC', news_url='http://feeds.bbci.co.uk/news/world/rss.xml')

        testuser_news_sites = UserNewsSite.objects.create(user=cls.testuser)
        testuser_news_sites.news_sites.add(BBC)

        newssite = NewsSite.objects.filter(news_site='BBC')[0]
        feed_item = update_news(newssite.news_url)[0]
        cls.newssite_name = newssite.news_site
        cls.item_link = feed_item.link
        cls.item_title = feed_item.title
        UserNewsItem.objects.create(user=cls.testuser,
                                    news_site=newssite,
                                    title=cls.item_title,
                                    summary=feed_item.summary,
                                    link=cls.item_link,
                                    published=feedparser_time_to_datetime(feed_item),)

    def setUp(self):
        self.client.login(username='testuser', password='123')
        self.response = self.client.get(reverse('mynewsitems'))

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_form_correct_input(self):
        ''' The view must contain:
                3 <input>: csrf (2x), site btn
        '''
        self.assertContains(self.response, '<input', 3)

    def test_form_has_delete_button(self):
        self.assertContains(
            self.response,
            '<button class="btn btn-outline-secondary btn-sm" name="deleted_item_pk"')

    def test_link_to_newssite_name(self):
        self.assertContains(self.response, f'value="{self.newssite_name}"')

    def test_link_to_news_item_url(self):
        self.assertContains(self.response, f'href="{self.item_link}"')

    def test_display_of_item_title(self):
        title = convert_string_to_html(self.item_title)
        self.assertContains(self.response, title)

    def test_delete_news(self):
        data = {'deleted_item_pk': 1}
        _ = self.client.post(reverse('mynewsitems'), data)
        self.assertFalse(UserNewsItem.objects.filter(user=self.testuser))

    def test_redirect_to_newspage(self):
        data = {'site_btn': self.newssite_name}
        response = self.client.post(reverse('mynewsitems'), data)
        self.assertRedirects(response, reverse('newspage'))

    def test_create_html(self):
        file_name = 'newsfeed/tests/test_mynewsitems.html'
        with open(file_name, 'wt', encoding='utf-8') as f:
            f.write(self.response.content.decode())
