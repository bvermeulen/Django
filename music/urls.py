from django.urls import path
from .views import MusicView

urlpatterns = [
    path('music/music/', MusicView.as_view(), name='music'),
]
