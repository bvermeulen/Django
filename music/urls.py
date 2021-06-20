from django.urls import path
from .views import PlayTopTracksView, PlayListView

urlpatterns = [
    path('music/play_top_tracks/', PlayTopTracksView.as_view(), name='play_top_tracks'),
    path('music/playlist/', PlayListView.as_view(), name='playlist'),
]
