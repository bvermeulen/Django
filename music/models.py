# models for music app
from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE


class MusicTrack(models.Model):
    track_id = models.CharField(max_length=30)
    artist = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    preview_url = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"user: {self.user}: {self.track_id}, {self.artist}, {self.name}"

    class Meta:
        unique_together = ["track_id", "user"]
