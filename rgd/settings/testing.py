from typing import List

from .base import *  # noqa: F401, F403

SECRET_KEY = 'insecuresecret'
DEBUG = True
ALLOWED_HOSTS: List[str] = []
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
