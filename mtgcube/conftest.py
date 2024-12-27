import pytest

from mtgcube.users.models import User
from mtgcube.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
  settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
  return UserFactory()
