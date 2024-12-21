from enum import Enum
from django import forms


class SortChoices(Enum):
    ARTIST = (1, "Artist")
    ALBUM = (2, "Album")
    SONG = (3, "Song")
    DATE = (4, "Date")
    RANDOM = (5, "Random")


class MusicForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MusicForm, self).__init__(*args, **kwargs)

        sort_choices = [(v.value[0], v.value[1]) for v in SortChoices]
        self.fields["sort_choice"] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={"style": "width:20px; accent-color:grey"}),
            choices=sort_choices,
            required=False,
        )
        self.fields["track_pk"] = forms.IntegerField(required=False)
        self.fields["track_id"] = forms.CharField(max_length=50, required=False)
        self.fields["artist_query"] = forms.CharField(max_length=50, required=False)
