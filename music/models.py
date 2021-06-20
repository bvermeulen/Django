# models for music app
from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE


class MusicTrack(models.Model):
    track_id = models.CharField(max_length=30)
    track_artist = models.CharField(max_length=100)
    track_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'user: {self.user}: {self.track_id}, {self.track_artist}, {self.track_name}'

    class Meta:
        unique_together = ['track_id', 'user']

