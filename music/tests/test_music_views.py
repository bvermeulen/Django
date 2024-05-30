from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..models import MusicTrack
from ..views import PlayTopTracksView, PlayListView


class MusicTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        testuser = User.objects.create_user(
            username='testuser',
            email='testuser@aa.com',
            first_name='test_is_my_name',
            password='testuser_pw'
        )
        _ = MusicTrack.objects.create(
            user=testuser,
            track_id='1zwMYTA5nlNjZxYrvBB2pV',
            track_artist='Adele',
            track_name='Someone Like You',
        )


class TestPlayTopTracksView(MusicTests):

    def setUp(self):
        self.response = self.client.post(reverse('play_top_tracks'))

    def test_get_placeholder(self):
        response = self.client.get(reverse('play_top_tracks'))
        self.assertContains(response, 'placeholder="enter name artist ..."')

    def test_csrf_token(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves(self):
        view = resolve('/music/play_top_tracks/')
        self.assertEqual(view.func.view_class, PlayTopTracksView)

    def test_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_valid_artist_query(self):
        valid_artist = 'Adele'
        data = {'artist_query': valid_artist}
        response = self.client.post(reverse('play_top_tracks'), data)
        self.assertGreater(len(response.context['artist']['top_tracks']), 0)
        self.assertContains(response, f'placeholder="{valid_artist}"')

    def test_invalid_artist_query(self):
        invalid_artist = "~~~PietjePuk~~~"
        data = {'artist_query': invalid_artist}
        response = self.client.post(reverse('play_top_tracks'), data)
        self.assertEqual(len(response.context['artist']['top_tracks']), 0)
        self.assertContains(response, f'placeholder="{invalid_artist}"')

    def test_with_login(self):
        self.client.login(username='testuser', password='testuser_pw')
        data = {'artist_query': 'Adele'}
        response = self.client.post(reverse('play_top_tracks'), data)
        playlist_url = reverse('playlist')
        self.assertContains(response, f'href="{playlist_url}"')
        self.assertContains(response, 'add to')

    def test_view_adds(self):
        self.client.login(username='testuser', password='testuser_pw')
        data = {'artist_query': '', 'track_id': '7xdLNxZCtY68x5MAOBEmBq'}
        _ = self.client.post(reverse('play_top_tracks'), data)
        self.assertEqual(MusicTrack.objects.all()[1].track_name, 'All Along the Watchtower')

    def test_with_anomynous(self):
        data = {'artist_query': 'Adele'}
        response = self.client.post(reverse('play_top_tracks'), data)
        playlist_url = reverse('playlist')
        self.assertNotContains(response, f'href="{playlist_url}"')
        self.assertNotContains(response, 'add to')


class TestPlayListView(MusicTests):

    def setUp(self):
        self.client.login(username='testuser', password='testuser_pw')
        # note post redirects to get
        self.response = self.client.get(reverse('playlist'))

    def test_playlist_view_not_logged_in_redirects_to_login_page(self):
        self.client.logout()
        response = self.client.post(reverse('playlist'))
        login_url = reverse('login') + f'?next={reverse("playlist")}'
        self.assertRedirects(response, login_url, fetch_redirect_response=False)
        self.assertEqual(response.status_code, 302)

    def test_csrf_token(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves(self):
        view = resolve('/music/playlist/')
        self.assertEqual(view.func.view_class, PlayListView)

    def test_view_contains_link_to_toptracks(self):
        tracks_url = reverse('play_top_tracks')
        self.assertContains(self.response, f'href="{tracks_url}"')

    def test_view_contains_link_to_home_page(self):
        home_url = reverse('home')
        self.assertContains(self.response, f'href="{home_url}"')

    def test_view_contains_user_first_name(self):
        self.assertContains(self.response, 'Playlist test_is_my_name')

    def test_view_contains_delete(self):
        self.assertContains(self.response, 'delete from playlist')

    def test_view_deletes(self):
        track_pk = MusicTrack.objects.all()[0].pk
        data = {'track_pk': track_pk}
        _ = self.client.post(reverse('playlist'), data)
        self.assertEqual(len(MusicTrack.objects.all()), 0)
