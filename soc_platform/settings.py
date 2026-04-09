"""
Django settings for soc_platform project.
Federated SOC Threat Intelligence Platform.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-c#m+k2=e2)dzc3u@*8+*^icx+-%qa8l+o)*58z_p1ay#x*2kw%',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------- Application definition ----------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Project apps
    'users',
    'logs',
    'threat_detection',
    'federated',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'soc_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'soc_platform.wsgi.application'

# ---------- Database ----------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------- Auth ----------

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ---------- Internationalization ----------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------- Static files ----------

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------- Default primary key ----------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------- External Services (Docker / Environment) ----------

ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST', 'localhost')
ELASTICSEARCH_PORT = int(os.environ.get('ELASTICSEARCH_PORT', '9200'))
ELASTICSEARCH_SCHEME = os.environ.get('ELASTICSEARCH_SCHEME', 'http')

AGGREGATOR_HOST = os.environ.get('AGGREGATOR_HOST', 'localhost')
AGGREGATOR_PORT = int(os.environ.get('AGGREGATOR_PORT', '8081'))

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# ---------- Federated Learning ----------

FL_MIN_NODES = int(os.environ.get('FL_MIN_NODES', '2'))
FL_MAX_ROUNDS = int(os.environ.get('FL_MAX_ROUNDS', '100'))
FL_DEFAULT_EPSILON = float(os.environ.get('FL_DEFAULT_EPSILON', '1.0'))
FL_DEFAULT_DELTA = float(os.environ.get('FL_DEFAULT_DELTA', '1e-5'))
FL_MAX_EPSILON = float(os.environ.get('FL_MAX_EPSILON', '10.0'))
