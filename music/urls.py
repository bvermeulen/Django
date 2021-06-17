from django.urls import path
from .views import PlayTopTracksView

urlpatterns = [
    path('music/play_top_tracks/', PlayTopTracksView.as_view(), name='play_top_tracks'),
]
