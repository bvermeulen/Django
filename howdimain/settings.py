"""
Django settings for howdimain project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from decouple import config, Csv
from howdimain.utils.plogger import Logger
from howdimain.howdimain_vars import (
    TEXT_VERIFICATION_SUCCESS_MESSAGE,
    TEXT_VERIFICATION_FAILED_MESSAGE,
)

logformat = "%(asctime)s:%(levelname)s:%(message)s"
Logger.set_logger(config("LOG_FILE"), logformat, "INFO")
logger = Logger.getlogger()
HOWDIMAIN_VERSION = (
    "https://github.com/bvermeulen/Django/tree/howdimain-digitalocean_v9"
)
HOWDIMAIN_DATE = "February, 2024: implement captcha and email verification"
HOWDIMAIN_AUTHOR = "bruno.vermeulen@hotmail.com"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]

WSGI_APPLICATION = "howdimain.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "captcha",
    "verify_email.apps.VerifyEmailConfig",
    "widget_tweaks",
    "martor",
    "crispy_forms",
    "crispy_bootstrap4",
    "accounts",
    "boards",
    "newsfeed",
    "stock",
    "music",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "howdimain.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "localhost",
        "PORT": config("DB_PORT"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
    },
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # },
}
# when testing set CAPTCHA_TEST_MODE to True
CAPTCHA_TEST_MODE = False

# Email settings
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = "<noreply@howdiweb.nl>"
EMAIL_SUBJECT_PREFIX = "[Howdiweb] "

# Verificatio_email settings
EXPIRE_AFTER = "1d"
SUBJECT = "Howdimain verification email"
HTML_MESSAGE_TEMPLATE = "accounts/verification_email_msg.html"
VERIFICATION_SUCCESS_TEMPLATE = "accounts/verification_successful.html"
VERIFICATION_SUCCESS_MSG = TEXT_VERIFICATION_SUCCESS_MESSAGE
VERIFICATION_FAILED_TEMPLATE = "accounts/verification_failed.html"
VERIFICATION_FAILED_MSG = TEXT_VERIFICATION_FAILED_MESSAGE
LINK_EXPIRED_TEMPLATE = "accounts/verification_link_expired.html"
REQUEST_NEW_EMAIL_TEMPLATE = "accounts/verification_request_new_email.html"
NEW_EMAIL_SENT_TEMPLATE = "accounts/verification_new_email_sent.html"
MAX_RETRIES = 2

# Crispy settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
PASSWORD_VALIDATION = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{PASSWORD_VALIDATION}.UserAttributeSimilarityValidator"},
    {"NAME": f"{PASSWORD_VALIDATION}.MinimumLengthValidator"},
    {"NAME": f"{PASSWORD_VALIDATION}.CommonPasswordValidator"},
    {"NAME": f"{PASSWORD_VALIDATION}.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "media")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "home"
LOGIN_REDIRECT_URL = "home"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Spofity credetials
SPOTIFY_CLIENT_ID = config("SPOTIFY_CLIENT_ID", default="")
SPOTIFY_CLIENT_SECRET = config("SPOTIFY_CLIENT_SECRET", default="")
SPOTIFY_REDIRECT_URI = config("SPOTIFY_REDIRECT_URI", default="")

# Global martor settings
# Input: string boolean, `true/false`
MARTOR_ENABLE_CONFIGS = {
    "imgur": "true",  # to enable/disable imgur/custom uploader.
    "mention": "false",  # to enable/disable mention
    "jquery": "true",  # to include/revoke jquery (require for admin default django)
    "living": "false",  # to enable/disable live updates in preview
}

# To setup the martor editor with label or not (default is False)
MARTOR_ENABLE_LABEL = False

# Imgur API Keys
MARTOR_IMGUR_CLIENT_ID = config("IMGUR_CLIENT_ID")
MARTOR_IMGUR_API_KEY = config("IMGUR_SECRET_KEY")

# # Safe Mode
# MARTOR_MARKDOWN_SAFE_MODE = 'escape' # default

# Markdownify
MARTOR_MARKDOWNIFY_FUNCTION = "martor.utils.markdownify"  # default
MARTOR_MARKDOWNIFY_URL = "/martor/markdownify/"  # default

# Markdown extensions (default)
MARTOR_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.smarty",
    "markdown.extensions.fenced_code",
    # Custom markdown extensions.
    "martor.extensions.urlize",
    "martor.extensions.del_ins",  # ~~strikethrough~~ and ++underscores++
    "martor.extensions.mention",  # to parse markdown mention
    "martor.extensions.emoji",  # to parse markdown emoji
    "martor.extensions.mdx_video",  # to parse embed/iframe video
]

# Markdown Extensions Configs
MARTOR_MARKDOWN_EXTENSION_CONFIGS = {}

# Markdown urls
MARTOR_UPLOAD_URL = "/martor/uploader/"  # default
MARTOR_SEARCH_USERS_URL = "/martor/search-user/"  # default

# Markdown Extensions
# MARTOR_MARKDOWN_BASE_EMOJI_URL = 'https://www.webfx.com/tools/emoji-cheat-sheet/graphics/emojis/'     # from webfx                          #pylint: disable=line-too-long
MARTOR_MARKDOWN_BASE_EMOJI_URL = "https://github.githubassets.com/images/icons/emoji/"  # default from github                 #pylint: disable=line-too-long
# MARTOR_MARKDOWN_BASE_MENTION_URL = 'https://python.web.id/author/'                                    # please change this to your domain   #pylint: disable=line-too-long

nl = "\n"
logger.info(
    f"{nl}============================================================"
    f"{nl}Howdimain version: {HOWDIMAIN_VERSION}"
    f"{nl}Version date: {HOWDIMAIN_DATE}"
    f"{nl}Author: {HOWDIMAIN_AUTHOR}"
    f"{nl}Logfile: {config('LOG_FILE')}"
    f"{nl}Debug: {config('DEBUG')}"
    f"{nl}Alowed hosts: {ALLOWED_HOSTS}"
    f"{nl}------------------------------------------------------------"
)
logger.info(
    f"{nl}DB_NAME: {config('DB_NAME')}"
    f"{nl}DB_PORT: {config('DB_PORT')}"
    f"{nl}DB_USER: {config('DB_USER')}"
    f"{nl}DB_PASSWORD: XXXXXXXXXX"
    f"{nl}EMAIL_BACKEND: {EMAIL_BACKEND}"
    f"{nl}EMAIL_HOST: {EMAIL_HOST}"
    f"{nl}EMAIL_PORT: {EMAIL_PORT}"
    f"{nl}EMAIL_HOST_USER: {EMAIL_HOST_USER}"
    f"{nl}EMAIL_HOST_PASSWORD: XXXXXXXXXX"
    f"{nl}EMAIL_USE_TLS: {EMAIL_USE_TLS}"
    f"{nl}IMGUR CLIENT ID: {MARTOR_IMGUR_CLIENT_ID}"
    f"{nl}============================================================"
)
