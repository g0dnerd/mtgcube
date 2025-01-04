from .base import *  # noqa
from .base import env

import io
import os

from google.cloud import secretmanager

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# [START gaeflex_py_django_secret_config]
env_file = os.path.abspath("config/settings/.env")

if os.path.isfile(env_file):
  print("using local .env file")
  # Use a local secret file, if provided

  env.read_env(env_file)
# [START_EXCLUDE]
elif os.getenv("TRAMPOLINE_CI", None):
  # Create local settings if running with CI, for unit testing

  placeholder = (
    f"SECRET_KEY=a\n"
    "GS_BUCKET_NAME=None\n"
    f"DATABASE_URL=sqlite://{os.path.join(BASE_DIR, 'db.sqlite3')}"
  )
  env.read_env(io.StringIO(placeholder))
# [END_EXCLUDE]
elif os.environ.get("GOOGLE_CLOUD_PROJECT", None):
  # Pull secrets from Secret Manager
  project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

  client = secretmanager.SecretManagerServiceClient()
  settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
  name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
  payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")

  env.read_env(io.StringIO(payload))
else:
  raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")
# [END gaeflex_py_django_secret_config]

DATABASES = {"default": env.db()}

# If the flag as been set, configure to use proxy
if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
  DATABASES["default"]["HOST"] = "127.0.0.1"
  DATABASES["default"]["PORT"] = 5432

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
  "*",
  "https://vault.mtg-cube.de/",
  "https://mtg-cube.de/",
  "https://vault-446014.ew.r.appspot.com/",
  "vault-446014.ew.r.appspot.com/",
  "https://storage.googleapis.com/",
  "http://localhost:8080",
  "http://localhost:8000",
  "localhost",
  "localhost:8080",
]

DEBUG = True

SECRET_KEY = env(
  "DJANGO_SECRET_KEY",
  default="AjNIClMIgFyRwJUO2jyRy1r97WipjVimYj0GMHzgyNSxF361leDFWduPbio1uJJc",
)

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
  "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
  "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
  "https://*.mtg-cube.de",
  "https://vault.mtg-cube.de",
  "https://*.mtg-cube.de/",
  "https://vault.mtg-cube.de/",
  "https://*.mtg-cube.de",
  "https://www.vault.mtg-cube.de",
  "https://*.mtg-cube.de/",
  "https://www.vault.mtg-cube.de/",
  "https://vault-446014.ew.r.appspot.com/",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
  "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)

SOCIALACCOUNT_STORE_TOKENS = True

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405
