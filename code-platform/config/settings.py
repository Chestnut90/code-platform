"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from os import environ
from pathlib import Path
from distutils.util import strtobool

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get("SECRET_KEY", "")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(strtobool(environ.get("DEBUG", "True")))

ALLOWED_HOSTS = ["localhost"]

# Application definition

_DEFAULT_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

_THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_yasg",
    "debug_toolbar",
    "django_extensions",
]

_CUSTOM_APPS = [
    "problems.apps.ProblemsConfig",
]

INSTALLED_APPS = _DEFAULT_APPS + _THIRD_PARTY_APPS + _CUSTOM_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.get("POSTGRES_NAME", "code_platform"),
        "USER": environ.get("POSTGRES_USER", "code_platform"),
        "PASSWORD": environ.get("POSTGRES_PASSWORD", "code_platform"),
        "HOST": environ.get("POSTGRES_HOST", "code_platform_postgres"),
        "PORT": environ.get("POSTGRES_PORT", "5432"),
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = "static_files/files/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# rest framework
REST_FRAMEWORK = {
    "PAGE_SIZE": 5,
}

# RabbitMQ
RABBITMQ_USER = environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_HOST = environ.get("RABBITMQ_HOST", "code_platform_rabbitmq")
RABBITMQ_PORT = environ.get("RABBITMQ_PORT", "5672")

# Celery Configuration Options
CELERY_TIMEZONE = "Asia/Seoul"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = "amqp://{}:{}@{}:{}".format(
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
)
CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_RESULT_BACKEND = "redis://localhost:6379"

# Redis Cache
REDIS_HOST = environ.get("REDIS_HOST", "code_platform_redis")
REDIS_PORT = environ.get("REDIS_PORT", "6379")
REDIS_CACHE_TTL = 60 * 5  # default 5 min
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",  # change to just redis
        "LOCATION": "redis://{}:{}".format(REDIS_HOST, REDIS_PORT),
        "TIMEOUT": REDIS_CACHE_TTL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# For debug,
DEBUG_PROBLEM_QUERY_DELAY = 1  # second
DEBUG_PROBLEM_CHECK_DELAY = 2  # second
DEBUG_REDIS_PROBLEM_TTL = 1 * 60 * 60  # seconds
DEBUG_REDIS_QUERY_TTL = 1 * 60 * 60  # seconds

# for debug_toolbar
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    "0.0.0.0",
    "localhost",
    # ...
]
