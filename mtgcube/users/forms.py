from django.contrib.auth import forms as admin_forms
from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django import forms as d_forms

User = get_user_model()


class UserChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(admin_forms.UserCreationForm):
    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class CustomSignupForm(SignupForm):

    display_name = d_forms.CharField(
        required=True,
        widget=d_forms.TextInput(attrs={
            'max_length': 255,
            'placeholder': _('The name you want other players to see'),
        }),
    )

    pronouns = d_forms.CharField(
        required=True,
        label = _("My Pronouns"),
        widget=d_forms.Select(
            choices=[
                ("n", _("Neither/don't want to say")),
                ("m", "he/him"),
                ("f", "she/her"),
                ("x", "they/them"),
            ]
        )
    )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)

        pronouns = self.cleaned_data.pop('pronouns')
        name = self.cleaned_data.pop('display_name')

        user.pronouns = pronouns
        user.name = name

        user.save()
        return user