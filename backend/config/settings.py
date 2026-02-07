"""
Django settings for PayPi-Bridge backend.
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# ============== BASE ==============
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root (one level up from backend/)
load_dotenv(BASE_DIR.parent / ".env")

# ================== STATIC / MEDIA ==================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Django procura static files em:
# 1. STATICFILES_DIRS (diretórios adicionais)
# 2. Cada app/static/ (padrão do Django)
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
# O logo está em: backend/app/paypibridge/static/paypibridge/img/logo.png
# Será servido como: /static/paypibridge/img/logo.png

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", os.getenv("DJANGO_SECRET", "dev-secret-key-change-me"))
DEBUG = os.getenv("DEBUG", os.getenv("ENV", "True")) == "True"

# Configuração para produção
if not DEBUG:
    # Configurações específicas para produção
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Hosts e CSRF - Configuração fixa para funcionar em qualquer ambiente
_allowed = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").strip().split(",")
if "69.169.102.84" not in _allowed:
    _allowed.append("69.169.102.84")

# Lista base de hosts permitidos
# Django aceita hosts que começam com ponto para permitir subdomínios
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',  # Permite qualquer subdomínio do Railway (Django valida corretamente)
    'paypi-bridge-development.up.railway.app',  # Domínio específico do Railway
] + [h.strip() for h in _allowed if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.railway.app',
    'http://*.railway.app',
]

# Configuração para Railway (proxy reverso)
# Railway passa o protocolo real através do header X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ============ APPS ============
INSTALLED_APPS = [
    # Django padrão
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceiros
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",

    # Seus apps
    "app.paypibridge",
]

# IMPORTANTÍSSIMO: não remova os finders padrão
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",  # <- necessário para achar /admin
]

# ========== MIDDLEWARE ==========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "app.paypibridge.middleware.logging.RequestIDMiddleware",  # Adiciona request ID
    "whitenoise.middleware.WhiteNoiseMiddleware",  # <- antes de CommonMiddleware
    "config.middleware.RailwayHostValidationMiddleware",  # Validação customizada de hosts Railway
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS antes de CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "app.paypibridge.middleware.logging.StructuredLoggingMiddleware",  # Logging estruturado
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"] if (BASE_DIR / "templates").exists() else [],
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

# ========== DATABASE ==========
# Suporte a DATABASE_URL (Railway, Heroku, etc.) ou variáveis individuais (DB_* ou PG*)


def _db_fallback():
    """Fallback: usa DB_* ou PGDATABASE/PGHOST/PGPASSWORD/PGPORT (padrão libpq)."""
    db_name = os.getenv("DB_NAME") or os.getenv("PGDATABASE", "paypibridge")
    db_user = os.getenv("DB_USER") or os.getenv("PGUSER", "postgres")
    db_password = os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD", "postgres")
    db_host = os.getenv("DB_HOST") or os.getenv("PGHOST", "localhost")
    db_port = os.getenv("DB_PORT") or os.getenv("PGPORT", "5432")
    sslmode = "disable" if ".railway.internal" in str(db_host) else os.getenv("DB_SSL_MODE", "prefer")
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
            "OPTIONS": {"sslmode": sslmode},
            "CONN_MAX_AGE": 600,
        }
    }


DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    # Parse DATABASE_URL (formato: postgresql://user:password@host:port/dbname)
    from urllib.parse import urlparse, unquote
    
    try:
        # Converter postgresql:// para postgres:// para urlparse (compatibilidade)
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgres://", 1)
        
        parsed = urlparse(db_url)
        
        # Extrair nome do banco (remove leading /)
        db_name = parsed.path[1:] if parsed.path.startswith("/") else parsed.path
        host = parsed.hostname or ""
        
        # sslmode: rede interna (postgres.railway.internal) não usa SSL;
        # hosts externos (proxy.rlwy.net, etc.) requerem SSL
        sslmode = os.getenv("DB_SSL_MODE")
        if sslmode is None:
            sslmode = "disable" if ".railway.internal" in host else "require"
        
        db_options = {"sslmode": sslmode}
        
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_name,
                "USER": parsed.username or "postgres",
                "PASSWORD": unquote(parsed.password) if parsed.password else "",
                "HOST": host,
                "PORT": str(parsed.port) if parsed.port else "5432",
                "OPTIONS": db_options,
                "CONN_MAX_AGE": 600,  # Pool de conexões (10 minutos)
            }
        }
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Database configurado via DATABASE_URL: {parsed.hostname}:{parsed.port}/{db_name}")
        
    except Exception as e:
        # Fallback para configuração padrão se parsing falhar
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao parsear DATABASE_URL: {e}. Usando configuração padrão.", exc_info=True)
        DATABASES = _db_fallback()
else:
    # Configuração usando variáveis individuais (DB_* ou PG*)
    DATABASES = _db_fallback()

# ========== INTERNATIONALIZATION ==========
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ========== CELERY CONFIGURATION ==========
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BEAT_SCHEDULE = {
    "monitor-soroban-events": {
        "task": "app.paypibridge.tasks.monitor_soroban_events",
        "schedule": 30.0,  # Every 30 seconds
    },
    "process-incomplete-payments": {
        "task": "app.paypibridge.tasks.process_incomplete_payments",
        "schedule": 300.0,  # Every 5 minutes
    },
    "update-fx-rates": {
        "task": "app.paypibridge.tasks.update_fx_rates",
        "schedule": 300.0,  # Every 5 minutes
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== I18N / TZ ==========
# TIME_ZONE já definido acima (antes de CELERY)
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== STATIC / MEDIA (final) ==========
# WhiteNoise storage
# Em desenvolvimento, usar storage simples para facilitar debug
if DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# WhiteNoise configuração adicional
WHITENOISE_USE_FINDERS = True  # Permite servir arquivos de STATICFILES_DIRS em desenvolvimento
WHITENOISE_AUTOREFRESH = DEBUG  # Recarrega automaticamente em desenvolvimento
# WhiteNoise root - garantir que serve de STATIC_ROOT
WHITENOISE_ROOT = STATIC_ROOT

# ========== LOGIN REDIRECTS ==========
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ========== LOGGING (structured) ==========
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "structured": {
            "format": "{levelname} {asctime} request_id={request_id} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "app.paypibridge": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ========== AUTH / DRF / JWT ==========
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    # Paginação padrão
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Schema
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,  # Gera novo refresh token a cada refresh
    "BLACKLIST_AFTER_ROTATION": True,  # Invalida refresh token antigo após rotação
    "UPDATE_LAST_LOGIN": True,  # Atualiza last_login do usuário
}

# CORS - Configuração fixa para funcionar em qualquer ambiente
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'https://*.railway.app',
        'http://*.railway.app',
    ]

CORS_ALLOW_CREDENTIALS = True

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "PayPi-Bridge API",
    "VERSION": "1.0.0",
}

# Pi Network (optional)
PI_API_KEY = os.getenv("PI_API_KEY", "")
PI_WALLET_PRIVATE_SEED = os.getenv("PI_WALLET_PRIVATE_SEED", "")
PI_NETWORK = os.getenv("PI_NETWORK", "Pi Testnet")

# CCIP / Webhooks
CCIP_WEBHOOK_SECRET = os.getenv("CCIP_WEBHOOK_SECRET", "")

# PPBridge Service
PPBRIDGE_API_KEY_ENABLED = os.getenv("PPBRIDGE_API_KEY_ENABLED", "false").lower() == "true"
PPBRIDGE_API_KEY = os.getenv("PPBRIDGE_API_KEY", "")
PPBRIDGE_WEBHOOK_HMAC_SECRET = os.getenv("PPBRIDGE_WEBHOOK_HMAC_SECRET", "")
PPBRIDGE_WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("PPBRIDGE_WEBHOOK_TIMEOUT_SECONDS", "5"))
PPBRIDGE_WEBHOOK_MAX_RETRIES = int(os.getenv("PPBRIDGE_WEBHOOK_MAX_RETRIES", "3"))
