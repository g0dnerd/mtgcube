from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Default user."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Display Name"), default="", max_length=255)

    NEITHER = "n"
    MALE = "m"
    FEMALE = "f"
    NONBINARY = "x"
    
    PRONOUN_CHOICES = {
        "n": _("neither/don't want to say"),
        "m": _("he/him"),
        "f": _("she/her"),
        "x": _("they/them"),
    }

    pronouns = CharField(
        "My Pronouns",
        max_length=1,
        choices=PRONOUN_CHOICES,
        default=NEITHER
    )

    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})