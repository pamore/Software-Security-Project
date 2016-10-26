"""
Django settings for group3_sbs project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import json

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#with open('/home/ubuntu/Documents/sbs_config.json') as data_file:
with open('/home/garrett/Documents/GitHub/sbs_config.json') as data_file:
    CONFIG = json.load(data_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = CONFIG['production_secret']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []#['www.group3sbs.mobicloud.asu.edu']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'login',
    'global_templates',
    'internal',
    'external',
    'reset',
    'create',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'global_templates.middleware.OneLoginPerUserMiddleware'
]

ROOT_URLCONF = 'group3_sbs.urls'

# Logging settings
# https://docs.djangoproject.com/en/1.10/topics/logging/
# https://github.com/jgutbub/CSE_545/wiki/Logging

SERVER_LOG_NAME = os.path.join(BASE_DIR, 'log/server_log.log')
LOGIN_LOG_NAME = os.path.join(BASE_DIR, 'log/login_log.log')
INTERNAL_LOG_NAME = os.path.join(BASE_DIR, 'log/internal_log.log')
EXTERNAL_LOG_NAME = os.path.join(BASE_DIR, 'log/external_log.log')
GLOBAL_TEMPLATES_LOG_NAME = os.path.join(BASE_DIR, 'log/global_templates_log.log')
CREATE_LOG_NAME = os.path.join(BASE_DIR, 'log/create_log.log')
RESET_LOG_NAME = os.path.join(BASE_DIR, 'log/reset_log.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(funcName)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': SERVER_LOG_NAME,
        },
        'login_handler': {
            'class': 'logging.FileHandler',
            'filename': LOGIN_LOG_NAME,
            'formatter': 'standard'
        },
        'internal_handler': {
            'class': 'logging.FileHandler',
            'filename': INTERNAL_LOG_NAME,
            'formatter': 'standard'
        },
        'external_handler': {
            'class': 'logging.FileHandler',
            'filename': EXTERNAL_LOG_NAME,
            'formatter': 'standard'
        },
        'global_templates_handler': {
            'class': 'logging.FileHandler',
            'filename': GLOBAL_TEMPLATES_LOG_NAME,
            'formatter': 'standard'
        },
        'create_handler': {
            'class': 'logging.FileHandler',
            'filename': CREATE_LOG_NAME,
            'formatter': 'standard'
        },
        'reset_handler': {
            'class': 'logging.FileHandler',
            'filename': RESET_LOG_NAME,
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'login': {
            'handlers': ['login_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'internal': {
            'handlers': ['internal_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'external': {
            'handlers': ['external_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'global_templates': {
            'handlers': ['global_templates_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'create': {
            'handlers': ['create_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'reset': {
            'handlers': ['reset_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Templates

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

WSGI_APPLICATION = 'group3_sbs.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'group3_sbs',
        'USER': 'root',
        'PASSWORD': CONFIG['database_password'],
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Atomtic HTTP Requests
ATOMIC_REQUESTS = True

AUTOCOMMIT = True

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Arizona'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')


# Axes Login settings
# https://django-axes.readthedocs.io/en/latest/configuration.html

AXES_LOGIN_FAILURE_LIMIT = 3
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = False

# Allow them retry after 1 hour
AXES_COOLOFF_TIME = 1
AXES_LOGGER = 'axes.watch_login'

# Choose the template (html) to be rendered when locked out
AXES_LOCKOUT_TEMPLATE = 'login/lockout.html'
AXES_LOCKOUT_URL = None

AXES_USERNAME_FORM_FIELD = 'username'
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = False
AXES_NEVER_LOCKOUT_WHITELIST = False


# Session settings
# https://docs.djangoproject.com/en/1.10/topics/http/sessions/

# 10 minute session life
SESSION_COOKIE_AGE = 600

# Delete session once browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Update the session life upon each request
SESSION_SAVE_EVERY_REQUEST = True


# Email Setup
# https://docs.djangoproject.com/en/1.10/topics/email/
# https://github.com/jgutbub/CSE_545/wiki/Sending-mail

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'group3sbs@gmail.com'
EMAIL_HOST_PASSWORD = CONFIG['email_password']
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

TEMPLATED_EMAIL_BACKEND = 'templated_email.backends.vanilla_django.TemplateBackend'

# Login
LOGIN_URL = "/login/"

# X Frames
X_FRAME_OPTIONS = 'DENY'

# Production Security Settings
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
