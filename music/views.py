import random
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from howdimain.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.plogger import Logger
from music.models import MusicTrack
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

logger = Logger.getlogger()


spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
))

class PlayTopTracksView(View):
    template_name = 'music/play_top_tracks.html'
    artist_empty = {'artist': 'enter name artist ...', 'top_tracks': []}

    def get(self, request):
        artist = request.session.get('artist', self.artist_empty)
        if not artist.get('top_tracks'):
            artist = self.artist_empty

        context = {
            'artist': artist
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        artist = request.session.get('artist', self.artist_empty)

        if request.method=='POST':
            artist_query = request.POST.get('artist_query')
            track_id = request.POST.get('track_id')

            if artist_query and artist_query != artist.get('artist'):
                artist_name = artist_query
                top_tracks = []
                try:
                    artists = spotify.search(q='artist:' + artist_query, type='artist')
                    top_tracks = spotify.artist_top_tracks(
                        artists['artists']['items'][0]['uri'][15:]
                    )['tracks'][:10]

                except Exception as e:
                    pass

                artist = {
                    'artist': artist_name,
                    'top_tracks': top_tracks,
                }
                request.session['artist'] = artist

            elif user.is_authenticated and track_id:
                try:
                    track_data = spotify.track(track_id)
                    MusicTrack.objects.create(
                        track_id=track_data.get('id'),
                        track_artist=track_data.get('artists')[0].get('name')[:100],
                        track_name=track_data.get('name')[:100],
                        user=user,
                    )
                    logger.info(
                        f'user {user} [ip: {get_client_ip(request)}] '
                        f'added {track_data.get("name")} to playlist')

                except (IntegrityError, SpotifyException):
                    pass

            else:
                pass

        else:
            pass

        context = {
            'artist': artist,
        }

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class PlayListView(View):
    template_name = 'music/playlist.html'

    def get(self, request):
        user = request.user
        track_list = list(MusicTrack.objects.filter(user=user))
        random.shuffle(track_list)

        context = {
            'track_list': track_list
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user

        if request.method=='POST':
            track_pk = request.POST.get('track_pk')
            try:
                track_to_be_deleted = MusicTrack.objects.get(pk=track_pk)
                logger.info(
                    f'user {user} [ip: {get_client_ip(request)}] '
                    f'removed {track_to_be_deleted.track_name} from playlist'
                )
                track_to_be_deleted.delete()

            except MusicTrack.DoesNotExist:
                pass

        return redirect(reverse('playlist'))
