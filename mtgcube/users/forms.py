from django.contrib.auth import forms as admin_forms
from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django import forms as d_forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML

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
    
class CustomSocialSignupForm(SocialSignupForm):
    display_name = d_forms.CharField(
        required=True,
        widget=d_forms.TextInput(attrs={
            'max_length': 255,
            'placeholder': _('Your username. Other players can see this.'),
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

    def __init__(self, *args, **kwargs):
        super(CustomSocialSignupForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        # Add magic stuff to redirect back.
        self.helper.layout.append(
            HTML(
                "{% if redirect_field_value %}"
                "<input type='hidden' name='{{ redirect_field_name }}'"
                " value='{{ redirect_field_value }}' />"
                "{% endif %}"
            )
        )

        # Add submit button like in original form.
        self.helper.layout.append(
            HTML(
                '<button class="btn btn-primary btn-block" type="submit">'
                '%s</button>' % _('Sign In')
            )
        )

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-xs-2 hide'
        self.helper.field_class = 'col-xs-8'

    def save(self, request):
        user = super(CustomSocialSignupForm, self).save(request)

        pronouns = self.cleaned_data.pop('pronouns')
        name = self.cleaned_data.pop('display_name')

        user.pronouns = pronouns
        user.name = name
        user.username = name

        user.save()
        return user