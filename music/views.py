import re
import random
import requests
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from howdimain.settings import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
)
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.plogger import Logger
from music.models import MusicTrack
from music.forms import MusicForm, SortChoices
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException


logger = Logger.getlogger()

SCOPE = "user-library-read"
CACHE = ".cache"
spotify_authorization = SpotifyOAuth(
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE,
    # show_dialog=True,
    # open_browser=False,
)
spotify = spotipy.Spotify(auth_manager=spotify_authorization)


class PlayTopTracksView(View):
    template_name = "music/play_top_tracks.html"
    artist_empty = {"artist": "enter name artist ...", "top_tracks": []}
    music_form = MusicForm

    def get(self, request):
        artist_dict = request.session.get("artist_dict", self.artist_empty)
        sort_choice = request.session.get("music_sort_choice", 1)

        if not artist_dict.get("top_tracks"):
            artist_dict = self.artist_empty

        music_form = self.music_form(
            initial={"sort_choice": sort_choice, "artist_dict": artist_dict}
        )
        context = {"music_form": music_form}
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        artist_dict = request.session.get("artist_dict", self.artist_empty)
        sort_choice = request.session.get("music_sort_choice", 1)
        top_tracks = []
        artist_object = {"name": ""}
        music_form = self.music_form(request.POST)

        if music_form.is_valid():
            artist_query = music_form.cleaned_data.get("artist_query")
            track_id = music_form.cleaned_data.get("track_id")

            if artist_query and artist_query != artist_dict.get("artist"):
                try:
                    artists = spotify.search(
                        q=artist_query,
                        type="artist",
                    )
                    artist_object = artists["artists"]["items"][0]
                    top_tracks = spotify.artist_top_tracks(artist_object["uri"])[
                        "tracks"
                    ][:10]
                    artist_dict = {
                        "artist": artist_object["name"],
                        "top_tracks": top_tracks,
                    }

                except Exception as e:
                    pass

            elif user.is_authenticated and track_id:
                try:
                    track_data = spotify.track(track_id, market="US")
                    embed_url = "".join(
                        ["https://open.spotify.com/embed/track/", track_id]
                    )
                    result = requests.session().get(embed_url)
                    content = str(result.content)
                    m = re.search(r"\"audioPreview\":{\"url\":\"(.*?)\"}", content)
                    try:
                        preview_url = m.group(1)

                    except IndexError:
                        preview_url = None

                    song = MusicTrack.objects.create(
                        track_id=track_id,
                        artist=track_data.get("artists")[0].get("name")[:100],
                        album=track_data.get("album").get("name")[:100],
                        name=track_data.get("name")[:100],
                        preview_url=preview_url[:100] if preview_url else "",
                        user=user,
                    )
                    song.store_image(
                        ".".join([song.track_id, "jpg"]),
                        track_data.get("album").get("images")[1].get("url"),
                    )
                    logger.info(
                        f"user {user} [ip: {get_client_ip(request)}] "
                        f"added {track_data.get("name")} to playlist"
                    )

                except (IntegrityError, SpotifyException):
                    pass

            else:
                pass

        else:
            pass

        music_form = self.music_form(
            initial={"artist_dict": artist_dict, "sort_choice": sort_choice}
        )
        request.session["artist_dict"] = artist_dict
        context = {"music_form": music_form}
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class PlayListView(View):
    template_name = "music/playlist.html"
    music_form = MusicForm

    def get(self, request, sort_choice):
        user = request.user
        request.session["music_sort_choice"] = sort_choice
        music_form = self.music_form(initial={"sort_choice": sort_choice})

        if SortChoices.ARTIST.value[0] == sort_choice:
            track_list = list(MusicTrack.objects.filter(user=user).order_by("artist"))
        elif SortChoices.ALBUM.value[0] == sort_choice:
            track_list = list(MusicTrack.objects.filter(user=user).order_by("album"))
        elif SortChoices.SONG.value[0] == sort_choice:
            track_list = list(MusicTrack.objects.filter(user=user).order_by("name"))
        elif SortChoices.DATE.value[0] == sort_choice:
            track_list = list(MusicTrack.objects.filter(user=user).order_by("added_at"))
        elif SortChoices.RANDOM.value[0] == sort_choice:
            track_list = list(MusicTrack.objects.filter(user=user))
            random.shuffle(track_list)
        else:
            track_list = list(MusicTrack.objects.filter(user=user).order_by("artist"))
        context = {"track_list": track_list, "music_form": music_form}
        return render(request, self.template_name, context)

    def post(self, request, sort_choice):
        user = request.user
        music_form = self.music_form(request.POST)

        if music_form.is_valid():
            new_sort_choice = music_form.cleaned_data.get("sort_choice")
            sort_choice = new_sort_choice if new_sort_choice else sort_choice
            track_pk = music_form.cleaned_data.get("track_pk")

            try:
                track_to_be_deleted = MusicTrack.objects.get(pk=track_pk)
                logger.info(
                    f"user {user} [ip: {get_client_ip(request)}] "
                    f"removed {track_to_be_deleted.name} from playlist"
                )
                track_to_be_deleted.delete()

            except MusicTrack.DoesNotExist:
                pass

        return redirect(reverse("playlist", kwargs={"sort_choice": sort_choice}))
