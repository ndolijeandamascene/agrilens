"""
Test settings for AgriLens.
"""
from .base import *

DEBUG = False
SECRET_KEY = 'test-secret-key-agrilens'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
