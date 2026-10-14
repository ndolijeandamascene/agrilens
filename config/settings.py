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

# Load .env file from repository root if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

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
    default=['localhost', '127.0.0.1', '[::1]']
)

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
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

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
    DATABASES = {
        'default': env.db('DATABASE_URL')
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

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
# Email Backend
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env.str('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# ------------------------------------------------------------------------------
# Production Security Hardening
# ------------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
