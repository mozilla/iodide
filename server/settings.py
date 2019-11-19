"""
Django settings for iodide server project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import re

import environ
import redis
from django.utils.log import DEFAULT_LOGGING
from furl import furl
from spinach.brokers.redis import RedisBroker, recommended_socket_opts

env = environ.Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.join(BASE_DIR, ".."))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("IODIDE_SERVER_DEBUG", default=False)

SITE_URL = env("SERVER_URI", default="http://localhost:8000/")
SITE_HOSTNAME = furl(SITE_URL).host
EVAL_FRAME_ORIGIN = env.str("EVAL_FRAME_ORIGIN", SITE_URL)
EVAL_FRAME_HOSTNAME = furl(EVAL_FRAME_ORIGIN).host
ALLOWED_HOSTS = list(set([SITE_HOSTNAME, EVAL_FRAME_HOSTNAME]))

# Special settings so staging servers can redirect to production
IS_STAGING = env.bool("IS_STAGING", default=False)
PRODUCTION_SERVER_URL = env.str("PRODUCTION_SERVER_URL", None)

# Define URI redirects.
# Is a ;-delimited list of redirects, where each section is of the form
# $prefix=$destination
IODIDE_REDIRECTS = env("IODIDE_REDIRECTS", default="")

# Dockerflow
DOCKERFLOW_ENABLED = env.bool("DOCKERFLOW_ENABLED", default=False)

# Social auth
SOCIAL_AUTH_GITHUB_KEY = env.str("GITHUB_CLIENT_ID", None)
SOCIAL_AUTH_GITHUB_SECRET = env.str("GITHUB_CLIENT_SECRET", None)
SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

# OpenIDC (aka auth0 identity/authentication)
USE_OPENIDC_AUTH = env.bool("USE_OPENIDC_AUTH", default=False)

# Use Gravatar middleware to display user avatars
USE_GRAVATAR = env.bool("USE_GRAVATAR", default=not SOCIAL_AUTH_GITHUB_KEY)

# Google analytics key (if unset, google analytics will be disabled)
GA_TRACKING_ID = env.str("GA_TRACKING_ID", None)

# Maximum file length for uploaded data / assets
MAX_FILENAME_LENGTH = 120
MAX_FILE_SIZE = 1024 * 1024 * 10  # 10 megabytes is the default

# Maximum length of file source URL
MAX_FILE_SOURCE_URL_LENGTH = 8192

# Minimum # of revisions for a notebook to show up in the index page list
MIN_FIREHOSE_REVISIONS = 10

# APPEND_SLASH = False

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # Disable Django's own staticfiles handling in favour of WhiteNoise, for
    # greater consistency between gunicorn and `./manage.py runserver`.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "social_django",
    "rest_framework",
    "rest_framework.authtoken",
    "server.base",
    "server.jwt",
    "server.notebooks",
    "server.files",
    "spinach.contrib.spinachd",
]

RESTRICT_API = env.bool("RESTRICT_API", default=False)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["server.permissions.RestrictedOrNot"],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if EVAL_FRAME_HOSTNAME != SITE_HOSTNAME:
    MIDDLEWARE.append("server.notebooks.middleware.NotebookEvalFrameMiddleware")

if DOCKERFLOW_ENABLED:
    INSTALLED_APPS.append("dockerflow.django")
    MIDDLEWARE.append("dockerflow.django.middleware.DockerflowMiddleware")

if USE_OPENIDC_AUTH:
    INSTALLED_APPS.append("server.openidc")
    MIDDLEWARE.append("server.openidc.middleware.OpenIDCAuthMiddleware")
elif SOCIAL_AUTH_GITHUB_KEY:
    MIDDLEWARE.extend(
        [
            "social_django.middleware.SocialAuthExceptionMiddleware",
            "server.github.middleware.GithubAuthMiddleware",
        ]
    )

if USE_GRAVATAR:
    MIDDLEWARE.append("server.gravatar.middleware.GravatarMiddleware")

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "server", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "server.context_processors.google_analytics",
                "server.context_processors.site_url",
            ]
        },
    }
]

LOGGING = DEFAULT_LOGGING.copy()
LOGGING["loggers"].update(
    {
        "spinach": {"handlers": ["console"], "level": "INFO"},
        "server": {"handlers": ["console"], "level": "INFO"},
    }
)

# When DEBUG is True, allow HTTP traffic, otherwise, never allow HTTP traffic.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default="31536000")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)

LOGIN_URL = "login"
LOGOUT_URL = "logout"
LOGIN_REDIRECT_URL = "login_success"

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", default="postgres://postgres@db/postgres")}
DB_REQUIRES_SSL = env.bool("DB_REQUIRES_SSL", default=not DEBUG)
if DB_REQUIRES_SSL:
    DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = "require"
DATABASES["default"].setdefault("CONN_MAX_AGE", 500)

AUTHENTICATION_BACKENDS = (
    "social_core.backends.github.GithubOAuth2"
    if SOCIAL_AUTH_GITHUB_KEY
    else "django.contrib.auth.backends.ModelBackend",
)

AUTH_USER_MODEL = "base.User"

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# openidc settings
OPENIDC_EMAIL_HEADER = env.str("OPENIDC_HEADER", default="HTTP_X_FORWARDED_USER")
OPENIDC_AUTH_WHITELIST = [
    re.compile(whitelist_re)
    for whitelist_re in env.str("OPENIDC_AUTH_WHITELIST", default="^/api").split(",")
    if whitelist_re
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Files in this directory will be served by WhiteNoise at the site root.
WHITENOISE_ROOT = os.path.join(ROOT, "build")
STATIC_ROOT = os.path.join(ROOT, "static")
STATIC_URL = SITE_URL
STATICFILES_DIRS = (os.path.join(BASE_DIR, "server", "static"),)

# Create hashed+gzipped versions of assets during collectstatic,
# which will then be served by WhiteNoise with a suitable max-age.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Add a MIME type for .wasm files (which is not included in WhiteNoise's defaults)
WHITENOISE_MIMETYPES = {".wasm": "application/wasm"}

REDIS_HOST = env.str("REDIS_HOST", default="redis")
REDIS_URL = env.str("REDIS_URL", default=f"redis://{REDIS_HOST}:6379/1")
SPINACH_BROKER = RedisBroker(redis.from_url(REDIS_URL, **recommended_socket_opts))

NOTEBOOK_REVISION_FIXED_WINDOW_LENGTH_SECS = 60
