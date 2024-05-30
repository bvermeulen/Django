from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views.newssites import newssites
from ..models import NewsSite, UserNewsSite

class NewsSitesTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser', email='testuser@mail.com', password='123')

    def test_newssites_url_resolves_newssites_view(self):
        view = resolve('/news/sites/')
        self.assertEqual(view.func, newssites)

    def test_newssites_view_contains_link_to_home_page(self):
        url = reverse('newssites')
        response = self.client.post(url, {}, follow=True)
        home_url = reverse('home')
        self.assertContains(response, f'href="{home_url}"')

    def test_newssites_view_not_logged_in_redirects_to_login_page(self):
        url = reverse('newssites')
        response = self.client.post(url, {})
        login_url = reverse('login') + f'?next={url}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

    def test_newssites_view_log_in_gives_status_code_200(self):
        self.client.login(username='testuser', password='123')
        url = reverse('newssites')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

    def test_newssites_view_log_has_correct_input(self):
        """
        The view must contain:
        6 <input>: csrf (2x), submit, news_site, news_url, submit
        """
        self.client.login(username="testuser", password="123")
        url = reverse("newssites")
        response = self.client.post(url, {})
        self.assertContains(response, "<input", 6)

    def test_newssites_view_valid_selected_redirects_to_newspage(self):
        newssite = NewsSite.objects.create(
            news_site='BBC', news_url='http://feeds.bbci.co.uk/news/world/rss.xml')
        test_usernewssite = UserNewsSite.objects.create(user=self.test_user)
        test_usernewssite.news_sites.add(newssite)

        self.client.login(username='testuser', password='123')
        data = {'selected_sites': [NewsSite.objects.first().pk]}
        url = reverse('newssites')
        response = self.client.post(url, data)

        newspage_url = reverse('newspage')
        self.assertRedirects(response, newspage_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

    def test_newssites_view_enter_valid_new_site(self):
        self.client.login(username='testuser', password='123')

        data = {'news_site': 'BBC',
                'news_url': 'http://feeds.bbci.co.uk/news/world/rss.xml'}
        url = reverse('newssites')
        response = self.client.post(url, data)

        # check if new_site is added to NewsSite
        self.assertEqual(NewsSite.objects.first().news_site, 'BBC')

        # and response gets back to 'newssites'
        self.assertEqual(response.status_code, 200)

    def test_newssites_view_enter_new_site_error_not_valid_RSS(self):
        self.client.login(username='testuser', password='123')

        data = {'news_site': 'BBC',
                'news_url': 'http://howdiweb.com'}
        url = reverse('newssites')
        response = self.client.post(url, data)
        # check if no new_site is added to NewsSite
        self.assertEqual(NewsSite.objects.count(), 0)

        # check correct error message
        self.assertContains(response, 'Site BBC did not return a valid RSS')

        # and response gets back to 'newssites'
        self.assertEqual(response.status_code, 200)

    def test_newssites_view_enter_new_site_error_existing_newssite(self):
        newssite = NewsSite.objects.create(
            news_site='BBC', news_url='http://feeds.bbci.co.uk/news/world/rss.xml')
        test_usernewssite = UserNewsSite.objects.create(user=self.test_user)
        test_usernewssite.news_sites.add(newssite)
        self.client.login(username='testuser', password='123')

        data = {'news_site': 'BBC',
                'news_url': 'http://feeds.bbci.co.uk/news/world/rss.xml'}
        url = reverse('newssites')
        response = self.client.post(url, data)

        # check if no new_site is added to NewsSite
        self.assertEqual(NewsSite.objects.count(), 1)

        # check correct error message
        self.assertContains(response, 'News site BBC already exists')

        # and response gets back to 'newssites'
        self.assertEqual(response.status_code, 200)

    def test_newssites_view_enter_new_site_error_url_not_properly_formed(self):
        self.client.login(username='testuser', password='123')

        data = {'news_site': 'BBC',
                'news_url': 'gooblie cook'}
        url = reverse('newssites')
        response = self.client.post(url, data)

        # check if no new_site is added to NewsSite
        self.assertEqual(NewsSite.objects.count(), 0)

        # check correct error message
        self.assertContains(response, 'URL gooblie cook is not properly formed')

        # and response gets back to 'newssites'
        self.assertEqual(response.status_code, 200)
