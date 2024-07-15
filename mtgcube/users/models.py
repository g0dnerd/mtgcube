from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

PRONOUNS_CHOICES = {
    "m": "he/him",
    "f": "she/her",
    "x": "they/them",
}

class User(AbstractUser):
    """Default user."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Display Name"), blank=True, max_length=255)


    pronouns = CharField("My Pronouns", blank=True, max_length=255, choices=PRONOUNS_CHOICES)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})