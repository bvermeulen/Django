from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from howdimain.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.plogger import Logger
from music.models import PlayList
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from pprint import pprint

logger = Logger.getlogger()

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
))

class PlayTopTracksView(View):
    template_name = 'music/play_top_tracks.html'

    def get(self, request):
        context = {
            'artist_query': 'enter name artist'
        }
        return render(request, self.template_name, context)

    def post(self, request):

        user = request.user
        if request.method=='POST':
            artist_query = request.POST.get('artist_query')
            track_id = request.POST.get('track_id')

            top_tracks = request.session.get('top_tracks', [])
            if artist_query:
                try:
                    artists = spotify.search(q='artist:' + artist_query, type='artist')
                    top_tracks = spotify.artist_top_tracks(
                        artists['artists']['items'][0]['uri'][15:]
                    )['tracks'][:10]

                except Exception as e:
                    pass

            else:
                artist_query = request.session.get('artist_query', '')

            if user.is_authenticated and track_id:
                try:
                    track_data = spotify.track(track_id)
                    PlayList.objects.create(
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

            request.session['artist_query'] = artist_query
            request.session['top_tracks'] = top_tracks

            context = {
                'top_tracks': top_tracks,
                'artist_query': artist_query,
            }

        else:
            context = {
                'artist_query': 'enter name artist',
            }

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class PlayListView(View):
    template_name = 'music/playlist.html'

    def get(self, request):
        user = request.user
        track_list = PlayList.objects.filter(user=user)
        context = {
            'track_list': track_list
        }
        return render(request, self.template_name, context)
