"""
Django settings for stable project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

# LOGGING_CONFIG = "barnlog.logging.logging_config"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{asctime} [{levelname:5}] {name} - {message}",
            "style": "{",
        },
        "json": {
            "class": "barnlog.logging.JsonFormatter",
            "format": "{asctime} [{levelname:5}] {name} - {message}",
            "style": "{",
        },

    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            # "formatter": "default"
            "formatter": "json"
        },
        "http": {
            "level": "DEBUG",
            "class": "barnlog.logging.HTTPHandler",
            "formatter": "json",
            "host": "localhost:8000",
            "url": "/log/ingest",
        },
    },
    "loggers": {
        # "access": {"handlers": ["console"], "propagate": False},
        # "console": {"handlers": ["console"], "propagate": False},
        # "ingest": {"handlers": ["console"], "propagate": False},
        # "celery": {"handlers": ["http"]},
        # "django": {"handlers": ["console"], "propagate": False}
        # "barnlog.http_client": {"handlers": ["http"]},
    },
    "root": {"level": "INFO", "handlers": ["console"]}
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-y629n4ks%*6g!g8#r*m_sx3f%r*7#ox_n$g@d6!$sz#!#dixq2"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "tests.stable.stall",
]

MIDDLEWARE = [
    "barnlog.django.request_id_middleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "barnlog.django.access_log_middleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tests.stable.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "tests.stable.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "TIME_ZONE": "UTC",
        "OPTIONS": {
            "timeout": 600,
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000

# CELERY
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}/2"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TIMEZONE = "UTC"
