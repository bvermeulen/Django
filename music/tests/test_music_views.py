from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..models import PlayList
from ..views import PlayTopTracksView

class MusicTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        testuser = User.objects.create(
            username='testuser',
            email='testuser@aa.com',
            password='testuser_pw'
        )

class PlayTopTracksView(MusicTests):

    def setUp(self):
        self.response = self.client.post(reverse('play_top_tracks'))

    def test_csrf_token(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves(self):
        view = resolve('/play_top_tracks/')
        self.assertEqual(view.func, PlayTopTracksView.as_view())

    def test_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_artist_query(self):
        data = {'artist_query': 'Adele'}
        response = self.client.post(reverse('play_top_tracks'), data)
        self.assertEqual('2', response.context['status'][11:12])

    def test_track(self):
        data = {'track': '1234567890'}
        response = self.client.post(reverse('play_top_tracks'), data)
        self.assertEqual('2', response.context['status'][11:12])
