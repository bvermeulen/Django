import datetime
import base64
import requests
import json
from decouple import config

SPOTIFY_CLIENT_ID = config("SPOTIFY_CLIENT_ID", default="")
SPOTIFY_CLIENT_SECRET = config("SPOTIFY_CLIENT_SECRET", default="")
CACHE_PATH = ".cache"


def refresh_the_token(refresh_token):

    auth_client = SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET
    auth_encode = "Basic " + base64.urlsafe_b64encode(auth_client.encode()).decode()

    headers = {
        "Authorization": auth_encode,
    }

    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    form = {"grant_type": "client_credentials"}

    response = requests.post(
        "https://accounts.spotify.com/api/token", data=data, headers=headers
    )

    if response.status_code == 200:
        # print(
        #    "The request to went through we got a status 200; Spotify token refreshed"
        # )
        response_json = response.json()
        new_token = response_json["access_token"]
        new_expire = response_json["expires_in"]
        # print(
        #    f"new access token: {new_token}, time left on new token is:  {new_expire / 60} min"
        # )
        return new_token

    else:
        print(f"ERROR! The response we got was: {response}")


if __name__ == "__main__":
    with open(CACHE_PATH, "r") as cache_file:
        cache = json.load(cache_file)

    print(f"{cache=}")
    print()
    access_token = refresh_the_token(cache["refresh_token"])
    cache["access_token"] = access_token
    cache["expires_at"] = int(
        (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        ).total_seconds()
        + cache["expires_in"]
    )
    print(f"{cache=}")
    with open(CACHE_PATH, "w") as cache_file:
        json.dump(cache, cache_file)
