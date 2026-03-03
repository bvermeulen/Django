import base64
import datetime
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from howdimain.settings import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
)
from howdimain.utils.plogger import Logger

logger = Logger.getlogger()
SCOPE = "user-library-read"
CACHE_FILE = ".cache"


def refresh_token_spotify():
    with open(CACHE_FILE, "r") as cache_file:
        cache = json.load(cache_file)
    
    if datetime.datetime.now(datetime.UTC).timestamp() > cache["expires_at"]:
        auth_client = SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET
        auth_encode = "Basic " + base64.urlsafe_b64encode(auth_client.encode()).decode()
        headers = {"Authorization": auth_encode}
        data = {"grant_type": "refresh_token", "refresh_token": cache["refresh_token"]}
        response = requests.post(
            "https://accounts.spotify.com/api/token", data=data, headers=headers
        )
        if response.status_code == 200:
            response_json = response.json()
            access_token = response_json["access_token"]
            cache["access_token"] = access_token
            with open(CACHE_FILE, "w") as cache_file:
                json.dump(cache, cache_file)
        
        else:
            logger.warning(f"refresh_token: {response.status_code=}")


def authorize_spotify():
    spotify_authorization = SpotifyOAuth(
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_FILE,
        # show_dialog=True,
        # open_browser=False,
    )
    spotify = spotipy.Spotify(auth_manager=spotify_authorization)
    return spotify
