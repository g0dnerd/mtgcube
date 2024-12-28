from .base import *  # noqa
from .base import env

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
  "http://127.0.0.1:8080"
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
