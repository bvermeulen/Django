# models for music app
import urllib
import urllib.request
from django.db import models
from django.core.files import File
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE


class MusicTrack(models.Model):
    track_id = models.CharField(max_length=30)
    artist = models.CharField(max_length=100)
    album = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    preview_url = models.CharField(max_length=100)
    song_image = models.ImageField(upload_to="spotify_images", blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def store_image(self, name, url):
        if self.track_id:
            result = urllib.request.urlretrieve(url)
            self.song_image.save(name, File(open(result[0], "rb")))
            self.save()

    @property
    def image_url(self):
        if self.song_image:
            return getattr(self.song_image, "url", None)
        return None

    def __str__(self):
        return f"user: {self.user}: {self.track_id}, {self.artist}, {self.name}"

    class Meta:
        unique_together = ["track_id", "user"]
