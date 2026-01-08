from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure `backend/.env` wins over any pre-set environment variables to avoid
# confusing "it looks correct but Graph still fails" situations.
load_dotenv(BASE_DIR / ".env", override=True)

# Logging
DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
GRAPH_LOG_LEVEL = os.getenv("GRAPH_LOG_LEVEL", "INFO")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
API_DEBUG_ERRORS = os.getenv("API_DEBUG_ERRORS", "1" if DEBUG else "0") == "1"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

ALLOW_NON_TLD_EMAILS = os.getenv("ALLOW_NON_TLD_EMAILS", "1" if DEBUG else "0") == "1"
ALLOW_NUMERIC_PASSWORDS = os.getenv("ALLOW_NUMERIC_PASSWORDS", "1" if DEBUG else "0") == "1"

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4210,http://127.0.0.1:4200").split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts.apps.AccountsConfig',
    'profiles.apps.ProfilesConfig',
    'core.apps.CoreConfig',
    'boms.apps.BomsConfig',
    'notifications.apps.NotificationsConfig',
    'catalog.apps.CatalogConfig',
    'purchase_orders.apps.PurchaseOrdersConfig',
    'attachments.apps.AttachmentsConfig',
    'searches.apps.SearchesConfig',
    'assets.apps.AssetsConfig',
    'transfers.apps.TransfersConfig',
    'bills.apps.BillsConfig',
    'feedback.apps.FeedbackConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'procurement_tool.urls'

ASGI_APPLICATION = "procurement_tool.asgi.application"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'procurement_tool.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

_db_engine = os.getenv("DJANGO_DB_ENGINE", "sqlite").lower()
if _db_engine == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "procurement"),
            "USER": os.getenv("POSTGRES_USER", "procurement"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "procurement"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

if ALLOW_NUMERIC_PASSWORDS:
    AUTH_PASSWORD_VALIDATORS = [
        v
        for v in AUTH_PASSWORD_VALIDATORS
        if v["NAME"] != "django.contrib.auth.password_validation.NumericPasswordValidator"
    ]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "core.exceptions.exception_handler",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "procurement-tool",
    }
}

# Microsoft Graph mail settings (read by core.graph_mailer)
GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
GRAPH_SENDER = os.getenv("GRAPH_SENDER", "")
GRAPH_SAVE_TO_SENT_ITEMS = os.getenv("GRAPH_SAVE_TO_SENT_ITEMS", "0") == "1"
GRAPH_TIMEOUT_SECONDS = int(os.getenv("GRAPH_TIMEOUT_SECONDS", "30"))
GRAPH_MAX_RETRIES = int(os.getenv("GRAPH_MAX_RETRIES", "3"))
GRAPH_RETRY_BACKOFF_SECONDS = float(os.getenv("GRAPH_RETRY_BACKOFF_SECONDS", "1.0"))

# In-app notifications can optionally be mirrored to email (best-effort).
NOTIFICATIONS_SEND_EMAIL = os.getenv("NOTIFICATIONS_SEND_EMAIL", "0") == "1"
# Temporary request logging for frontend polling verification.
NOTIFICATIONS_POLL_LOG = os.getenv("NOTIFICATIONS_POLL_LOG", "0") == "1"

# Purchase requests / BOMs
# 0 => unlimited drafts per user
BOM_MAX_DRAFTS_PER_USER = int(os.getenv("BOM_MAX_DRAFTS_PER_USER", "15"))

# Purchase Orders
PO_NUMBER_PREFIX = os.getenv("PO_NUMBER_PREFIX", "PO-")
PO_NUMBER_PADDING = int(os.getenv("PO_NUMBER_PADDING", "5"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": DJANGO_LOG_LEVEL},
        "core.graph_mailer": {"handlers": ["console"], "level": GRAPH_LOG_LEVEL, "propagate": False},
    },
}

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "").rstrip("/")


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
