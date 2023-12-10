"""
Django settings for letterpress project.

For use with Django 10.6 and 1.11
"""

import environ
import os
import platform

env = environ.Env(
    # set casting, default value
    CIRCLECI=(bool, False),
    CIRCLECI_ELASTICSEARCH_USER=(str, ''),
    CIRCLECI_ELASTICSEARCH_PASSWORD=(str, '')
)

# If this is running under CircleCI, then settings_secret won't be available
CIRCLECI = env('CIRCLECI')
if not CIRCLECI:
    from letterpress.firstrun import settings_secret

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
# When using Docker, make sure DB_DIR is set to wherever Docker looks for it ('/db/' for example)
# When not using Docker, root project directory is fine
DB_DIR = './'

# Settings stored in settings_secret
# SECURITY WARNING: keep the secret key used in production secret!
if CIRCLECI:
    SECRET_KEY = 'super-duper-secret-key-for-circleci'
    ALLOWED_HOSTS = []
else:
    SECRET_KEY = settings_secret.SECRET_KEY
    ALLOWED_HOSTS = settings_secret.ALLOWED_HOSTS

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_date_extensions',
    'django.forms',
    'sslserver',
    'tinymce',
    'letters',
    'letter_sentiment'
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

ROOT_URLCONF = 'letterpress.urls'
LOGOUT_REDIRECT_URL = '/'

# This was added to support custom GIS Admin map_template with Django 1.11
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),
                 'django/forms/templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'letterpress.wsgi.application'

# Database
DATABASES = {
    'default': {
        # This engine supports geodatabase functionality in Django
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(DB_DIR, 'db.sqlite3'),
    }
}
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# By default, staticfiles will look for files within the static/ directory of each installed app,
# as well as in directories defined in STATICFILES_DIRS.
STATIC_ROOT = os.path.join(BASE_DIR, 'letters/static')
STATIC_URL = '/static/'

# Configuration for django-tinymce
# Don't bother with TINYMCE_JS_ROOT
# Just let it use the defaults and find everything in static/tiny_mce
TINYMCE_JS_URL = os.path.join(STATIC_URL, 'tinymce/tinymce.min.js')
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, 'tinymce')
TINYMCE_DEFAULT_CONFIG = {
    'plugins': 'paste,searchreplace',
    'theme': 'silver',
    'width': '49em',
    'height': '18em',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'valid_styles': {
        '*': 'text-decoration',
    },
    'browser_spellcheck': True,
}

# Compressor stopped working, maybe when I upgraded some other package or
# switched to django-sslserver, so I had to set it to false
TINYMCE_COMPRESSOR = False

# Security stuff
# SecurityMiddleware redirects all non-HTTPS requests to HTTPS (except for those URLs matching a regular
# expression listed in SECURE_REDIRECT_EXEMPT).
SECURE_SSL_REDIRECT = True
# Use a secure cookie for the session cookie
SESSION_COOKIE_SECURE = True
# Use a secure cookie for the CSRF cookie
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
# Set the HTTP Strict Transport Security header on all responses that do not already have it.
# When enabling HSTS, it's a good idea to first use a small value for testing, for example, SECURE_HSTS_SECONDS = 3600
# for one hour. Each time a Web browser sees the HSTS header from your site, it will refuse to communicate non-securely
# (using HTTP) with your domain for the given period of time. Once you confirm that all assets are served securely on
# your site (i.e. HSTS didn't break anything), it's a good idea to increase this value so that infrequent visitors will
# be protected (31536000 seconds, i.e. 1 year, is common).
SECURE_HSTS_SECONDS = 3600
# Do I want this or not?
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# For django.middleware.clickjacking.XFrameOptionsMiddleware, default is "SAMEORIGIN"
X_FRAME_OPTIONS = "DENY"

# Elasticsearch URL: If using Docker, host needs to be the name of the service in the docker-compose file,
# otherwise it should be localhost if running locally
if CIRCLECI:
    ELASTICSEARCH_URL = 'http://localhost:9200/'
    ELASTICSEARCH_USER = env('CIRCLECI_ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = env('CIRCLECI_ELASTICSEARCH_PASSWORD')
else:
    ELASTICSEARCH_URL = 'http://elasticsearch:9200/'
    ELASTICSEARCH_USER = settings_secret.ELASTICSEARCH_USER
    ELASTICSEARCH_PASSWORD = settings_secret.ELASTICSEARCH_PASSWORD
