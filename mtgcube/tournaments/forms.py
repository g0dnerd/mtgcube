from django import forms
from .models import Image

from django.utils.translation import gettext_lazy as _

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        label = _('Image')
        fields = ['image']

    image = forms.ImageField()

class ReportResultForm(forms.Form):
    match_id = forms.CharField(widget=forms.HiddenInput())
    player1_wins = forms.ChoiceField(choices=[(i, str(i)) for i in range(3)])
    player2_wins = forms.ChoiceField(choices=[(i, str(i)) for i in range(3)])

    def clean(self):
        cleaned_data = super().clean()
        p1w = cleaned_data.get("player1_wins")
        p2w = cleaned_data.get("player2_wins")
        if int(p1w) + int(p2w) > 3:
            raise forms.ValidationError(
                _("Total wins cannot be greater than 3.")
            )

class ConfirmResultForm(forms.Form):
    match_id = forms.CharField(widget=forms.HiddenInput())