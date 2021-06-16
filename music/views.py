import datetime
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from howdimain.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.plogger import Logger
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

logger = Logger.getlogger()

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
))

class MusicView(View):
    template_name = 'music/music.html'

    def get(self, request):
        context = {
            'artist_query': 'enter name artist'
        }
        return render(request, self.template_name, context)

    def post(self, request):

        if request.method=='POST':
            artist_query = request.POST.get('artist_query')
            try:
                artists = spotify.search(q='artist:' + artist_query, type='artist')
                top_tracks = spotify.artist_top_tracks(
                    artists['artists']['items'][0]['uri'][15:]
                )['tracks'][:10]

            except Exception as e:
                top_tracks = []

            context = {
                'top_tracks': top_tracks,
                'artist_query': artist_query,
            }

        else:
            context = {
                'artist_query': 'enter name artist',
            }

        return render(request, self.template_name, context)
