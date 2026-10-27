"""
AgriLens Unified Django Settings.
2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity.
Configured dynamically via environment variables (.env).
"""
import os
from pathlib import Path
import environ

# Build paths inside the project: BASE_DIR is the workspace root
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ helper
env = environ.Env()

# Load environment file (.env, .env.pro, or file defined by ENV_FILE)
env_file_name = os.getenv('ENV_FILE')
if env_file_name and (BASE_DIR / env_file_name).exists():
    environ.Env.read_env(BASE_DIR / env_file_name)
elif (BASE_DIR / '.env').exists():
    environ.Env.read_env(BASE_DIR / '.env')
elif (BASE_DIR / '.env.pro').exists():
    environ.Env.read_env(BASE_DIR / '.env.pro')

# ------------------------------------------------------------------------------
# Core Settings
# ------------------------------------------------------------------------------
DEBUG = env.bool('DEBUG', default=True)

SECRET_KEY = env.str(
    'SECRET_KEY',
    default='django-insecure-dev-key-agrilens-rwanda-agricultural-platform-2026'
)

ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=[
        'localhost',
        '127.0.0.1',
        '[::1]',
        'testserver',
        'agrilens.ndoli.dev',
        'www.agrilens.ndoli.dev',
        '62.171.182.99',
    ]
)
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# CSRF Trusted Origins (Mandatory for Django 4/5 form submissions over HTTPS)
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'https://agrilens.ndoli.dev',
        'http://agrilens.ndoli.dev',
        'https://www.agrilens.ndoli.dev',
        'http://www.agrilens.ndoli.dev',
        'http://62.171.182.99',
    ]
)

# CORS Origins
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[
        'https://agrilens.ndoli.dev',
        'https://www.agrilens.ndoli.dev',
    ]
)
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)

# ------------------------------------------------------------------------------
# Application Definition
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.accounts.apps.AccountsConfig',
    'apps.geography.apps.GeographyConfig',
    'apps.agriculture.apps.AgricultureConfig',
    'apps.farmers.apps.FarmersConfig',
    'apps.surveys.apps.SurveysConfig',
    'apps.inputs.apps.InputsConfig',
    'apps.markets.apps.MarketsConfig',
    'apps.indicators.apps.IndicatorsConfig',
    'apps.dashboard.apps.DashboardConfig',
    'apps.api.apps.ApiConfig',
    'apps.data_management.apps.DataManagementConfig',
    'apps.decision_support.apps.DecisionSupportConfig',
    'apps.ml.apps.MlConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.insights.apps.InsightsConfig',
    'apps.assistant.apps.AssistantConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ------------------------------------------------------------------------------
# Machine Learning & Model Registry Configuration
# ------------------------------------------------------------------------------
ML_MODEL_DIR = BASE_DIR / 'data' / 'models'
ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)





MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.menu_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ------------------------------------------------------------------------------
# Database Configuration (DATABASE_URL from .env with SQLite fallback)
# ------------------------------------------------------------------------------
import sys

if 'test' in sys.argv or any('pytest' in arg for arg in sys.argv):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif env.str('DATABASE_URL', default=''):
    db_config = env.db('DATABASE_URL')
    db_config['CONN_MAX_AGE'] = env.int('DATABASE_CONN_MAX_AGE', default=60)
    db_config.setdefault('OPTIONS', {})
    db_config['OPTIONS'].setdefault('connect_timeout', 10)
    DATABASES = {
        'default': db_config
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ------------------------------------------------------------------------------
# Password Validation & Custom User Model
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

# ------------------------------------------------------------------------------
# Internationalization (Rwanda Standard Time)
# ------------------------------------------------------------------------------
LANGUAGE_CODE = env('LANGUAGE_CODE', default='en-us')
TIME_ZONE = env('TIME_ZONE', default='Africa/Kigali')
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# Static & Media Files
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ------------------------------------------------------------------------------
# Cache Configuration
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'agrilens-core-cache',
        'TIMEOUT': 900,  # 15 minutes default TTL
        'OPTIONS': {
            'MAX_ENTRIES': 2000,
        }
    }
}

# 1-year browser cache header for hashed static assets
WHITENOISE_MAX_AGE = env.int('WHITENOISE_MAX_AGE', default=31536000)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# ------------------------------------------------------------------------------
# Email Configuration (SMTP / Notifications)
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env.str(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend' if not DEBUG else 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = env.str('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='AgriLens Rwanda <ndolijeandamascene3@gmail.com>')
SERVER_EMAIL = env.str('SERVER_EMAIL', default='ndolijeandamascene3@gmail.com')

# ------------------------------------------------------------------------------
# Production Security Hardening & Proxy Support
# ------------------------------------------------------------------------------
# Trust proxy headers when behind Nginx, Easypanel, Traefik, or Caddy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Optional Sentry Monitoring
SENTRY_DSN = env.str('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
        )
    except Exception:
        pass

# ------------------------------------------------------------------------------
# AgriLens AI In-Process Local Neural LLM (llama-cpp-python)
# ------------------------------------------------------------------------------
QWEN_LLM_ENABLED = env.bool('QWEN_LLM_ENABLED', default=True)
QWEN_MODEL_PATH = env.str(
    'QWEN_MODEL_PATH',
    default='/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf' if os.name != 'nt' else r'C:\Users\ndoli\Documents\WEBAPP\IHKIP\models\qwen2.5-3b-instruct-q4_k_m.gguf'
)
QWEN_MODEL_N_CTX = env.int('QWEN_MODEL_N_CTX', default=2048)
QWEN_MODEL_N_THREADS = env.int('QWEN_MODEL_N_THREADS', default=2)
QWEN_MODEL_TEMPERATURE = env.float('QWEN_MODEL_TEMPERATURE', default=0.3)
QWEN_MODEL_MAX_TOKENS = env.int('QWEN_MODEL_MAX_TOKENS', default=350)
DOWNLOAD_QWEN_MODEL = env.bool('DOWNLOAD_QWEN_MODEL', default=True)

