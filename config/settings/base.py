"""
Base settings to build other settings files upon.
"""

# from django.utils.translation import ugettext_lazy as _
from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# mtgcube/
APPS_DIR = ROOT_DIR / "mtgcube"

env = environ.Env(DEBUG=(bool, False))

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
  # OS environment variables take precedence over variables from .env
  env.read_env(str(ROOT_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", True)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Europe/Berlin"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 2
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

LANGUAGES = (
  ("en", ("English")),
  ("de", ("German")),
)

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ROOT_DIR / "db.sqlite3",
  }
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

ACCOUNT_FORMS = {
  "signup": "mtgcube.users.forms.CustomSignupForm",
}

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "django.contrib.sessions",
  "django.contrib.sites",
  "django.contrib.messages",
  "django.contrib.staticfiles",
  "django.contrib.admin",
  "django.forms",
]
THIRD_PARTY_APPS = [
  "corsheaders",
  "crispy_forms",
  "crispy_bootstrap5",
  "allauth",
  "allauth.account",
  "allauth.socialaccount",
  "allauth.socialaccount.providers.google",
  "allauth.socialaccount.providers.facebook",
  "dynamic_breadcrumbs",
  "termsandconditions",
]

LOCAL_APPS = [
  "tournaments",
  "mtgcube.users.apps.UsersConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "mtgcube.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
  "django.contrib.auth.backends.ModelBackend",
  "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "users:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
  # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
  "django.contrib.auth.hashers.Argon2PasswordHasher",
  "django.contrib.auth.hashers.PBKDF2PasswordHasher",
  "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
  "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
  {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
  {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
  {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
  {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
  "corsheaders.middleware.CorsMiddleware",
  "django.middleware.security.SecurityMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.locale.LocaleMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "termsandconditions.middleware.TermsAndConditionsRedirectMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.common.BrokenLinkEmailsMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
  "allauth.account.middleware.AccountMiddleware",
]


# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
  "django.contrib.staticfiles.finders.FileSystemFinder",
  "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
  {
    # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
    "DIRS": [str(APPS_DIR / "templates")],
    "OPTIONS": {
      # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
      # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
      "loaders": [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
      ],
      # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
      "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.template.context_processors.i18n",
        "django.template.context_processors.media",
        "django.template.context_processors.static",
        "django.template.context_processors.tz",
        "django.contrib.messages.context_processors.messages",
        "mtgcube.utils.context_processors.settings_context",
        "dynamic_breadcrumbs.context_processors.breadcrumbs",
      ],
    },
  }
]

DYNAMIC_BREADCRUMBS_PATH_MAX_COMPONENT_LENGTH = 100
DYNAMIC_BREADCRUMBS_PATH_MAX_DEPTH = 7

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = (
  "bootstrap",
  "uni_form",
  "bootstrap3",
  "bootstrap4",
  "bootstrap5",
  "semantic-ui",
)

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
  "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,
  "formatters": {
    "verbose": {
      "format": "%(levelname)s %(asctime)s %(module)s "
      "%(process)d %(thread)d %(message)s"
    }
  },
  "handlers": {
    "console": {
      "level": "DEBUG",
      "class": "logging.StreamHandler",
      "formatter": "verbose",
    }
  },
  "root": {"level": "INFO", "handlers": ["console"]},
}

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "username"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = False
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "none"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "users.adapters.AccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "users.adapters.SocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_REQUIRED = False
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

CORS_ALLOW_ALL_ORIGINS = True
""" CORS_ALLOWED_ORIGINS = [
    "https://vault.mtg-cube.de",
    "https://*.mtg-cube.de",
    "https://mtg-cube.de",
    "https://storage.googleapis.com",
    "http://localhost",
    "http://localhost:8080"
] """

SOCIALACCOUNT_LOGIN_ON_GET = True

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_MIDDLEWARE_KEY_PREFIX = "mtg"

# ------------------------------------------------------------------------------
SOCIALACCOUNT_PROVIDERS = {
  "google": {
    "SCOPE": [
      "profile",
      "email",
    ],
    "AUTH_PARAMS": {
      "access_type": "online",
    },
    "OAUTH_PKCE_ENABLED": True,
    "FETCH_USERINFO": True,
  }
}

SOCIALACCOUNT_FORMS = {"signup": "users.forms.CustomSocialSignupForm"}

# Terms & Conditions (termsandconditions) Settings #######
DEFAULT_TERMS_SLUG = "privacy-policy"
ACCEPT_TERMS_PATH = "/terms/accept/"
TERMS_BASE_TEMPLATE = "terms_base.html"
TERMS_EXCLUDE_URL_PREFIX_LIST = {"/admin", "/terms"}
TERMS_EXCLUDE_URL_LIST = {"/termsrequired/", "/accounts/logout/", "/securetoo/"}
TERMS_EXCLUDE_URL_CONTAINS_LIST = {}  # Useful if you are using internationalization and your URLs could change per language
TERMS_CACHE_SECONDS = 0
# TERMS_EXCLUDE_USERS_WITH_PERM = "auth.can_skip_t&c"
TERMS_IP_HEADER_NAME = "REMOTE_ADDR"
TERMS_STORE_IP_ADDRESS = True
