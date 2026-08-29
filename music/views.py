import re
import random
import requests
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import View
from django.contrib.auth.models import User
from django.db import IntegrityError
from howdimain.utils.get_ip import get_client_ip
from howdimain.utils.plogger import Logger
from music.models import MusicTrack
from music.forms import MusicForm, SortChoices, ViewChoices
from howdimain.utils.spotify import client_spotify, authorize_spotify, SpotifyException, refresh_token_spotify


logger = Logger.getlogger()
spotify_client = client_spotify()
spotify = authorize_spotify()


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
        music_form = self.music_form(request.POST)

        if music_form.is_valid():
            artist_query = music_form.cleaned_data.get("artist_query")
            track_id = music_form.cleaned_data.get("track_id")
            refresh_token_spotify()

            if artist_query and artist_query != artist_dict.get("artist"):
                try:
                    results = spotify_client.search(
                        q=artist_query,
                        type="track",
                        limit=10
                    )
                    tracks = results.get("tracks", {}).get("items", [])
                    top_tracks = []
                    for track in tracks:
                        top_tracks.append(
                            {
                                "id": track.get("id"),
                                "uri": track.get("uri"),
                                "name": track.get("name"),
                                "album_name": (
                                    track.get("album", {}).get("name")
                                    if track.get("album")
                                    else None
                                ),
                                "preview_url": track.get("preview_url"),
                            }
                        )

                    artist_dict = {
                        "artist": artist_query,
                        "top_tracks": top_tracks,
                    }

                except Exception as e:
                    logger.warning(f"unable to get tracks from: {artist_query}")

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

class PlayListView(View):
    template_name = None
    music_form = MusicForm
    default_user = get_object_or_404(User, username="default_user")

    def get(self, request, sort_choice: int, view_choice: int):
        user = request.user
        if not user.is_authenticated:
            user = self.default_user

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

        if ViewChoices.SCROLL.value[0] == view_choice:
            self.template_name = "music/playlist_scroll.html"
        elif ViewChoices.SWIPE.value[0] == view_choice:
            self.template_name = "music/playlist_swipe.html"
        else:
            self.template_name = "music/playlist_scroll.html"

        music_form = self.music_form(initial={"sort_choice": sort_choice, "view_choice": view_choice})

        tracks = []
        for track in track_list:
            tracks.append(
                {
                    "pk": track.pk,
                    "track_id": track.track_id,
                    "name": track.name,
                    "artist": track.artist,
                    "album": track.album,
                    "image_url": track.image_url,
                    "preview_url": track.preview_url,
                }
            )

        context = {"track_list": tracks, "music_form": music_form}
        return render(request, self.template_name, context)

    def post(self, request, sort_choice: int, view_choice: int):
        user = request.user
        music_form = self.music_form(request.POST)

        if music_form.is_valid():
            sort_choice = request.session.get("music_sort_choice", 1)
            new_sort_choice = music_form.cleaned_data.get("sort_choice")
            sort_choice = new_sort_choice if new_sort_choice else sort_choice
            view_choice = request.session.get("view_choice", 1)
            new_view_choice = music_form.cleaned_data.get("view_choice")
            view_choice = new_view_choice if new_view_choice else view_choice
            track_pk = music_form.cleaned_data.get("track_pk")

            if user.is_authenticated:
                try:
                    track_to_be_deleted = MusicTrack.objects.get(pk=track_pk)
                    logger.info(
                        f"user {user} [ip: {get_client_ip(request)}] "
                        f"removed {track_to_be_deleted.name} from playlist"
                    )
                    track_to_be_deleted.delete()

                except MusicTrack.DoesNotExist:
                    pass

            request.session["sort_choice"] = sort_choice
            request.session["view_choice"] = view_choice
        return redirect(reverse("playlist", kwargs={"sort_choice":sort_choice, "view_choice":view_choice}))
