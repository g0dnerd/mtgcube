from django import forms
from .models import Image

from django.utils.translation import gettext_lazy as _

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        label = _('Image')
        fields = ['image']

    image = forms.ImageField()

