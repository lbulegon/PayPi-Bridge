import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_DIR = BASE_DIR / "backend" / "app"
if APP_DIR.exists() and str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

SECRET_KEY = os.getenv("DJANGO_SECRET", "insecure-change-me")
ENV = os.getenv("ENV", "dev").lower()
DEBUG = ENV != "prod"

allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS", "")
if allowed_hosts_env:
    ALLOWED_HOSTS = [
        host.strip() for host in allowed_hosts_env.split(",") if host.strip()
    ]
else:
    ALLOWED_HOSTS = ["*"] if DEBUG else []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "paypibridge",
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

ROOT_URLCONF = "setup.urls"

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

WSGI_APPLICATION = "setup.wsgi.application"
ASGI_APPLICATION = "setup.asgi.application"


def _database_from_url(url: str):
    parsed = urlparse(url)
    scheme = parsed.scheme
    if scheme in ("postgres", "postgresql"):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": parsed.port or "",
        }
    if scheme == "sqlite":
        if parsed.path in ("", "/"):
            name = BASE_DIR / "db.sqlite3"
        else:
            name = parsed.path.lstrip("/")
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name,
        }
    return None


db_url = os.getenv("DB_URL", "").strip()
db_config = _database_from_url(db_url) if db_url else None
if db_config:
    DATABASES = {"default": db_config}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PayPiBridge Pay API",
    "VERSION": "0.1.0",
}
