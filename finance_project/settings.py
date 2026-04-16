from pathlib import Path
import os
from logging.handlers import RotatingFileHandler
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Enable localization
USE_L10N = True
USE_I18N = True

# Set the default locale (German in this case)
LANGUAGE_CODE = 'de'

# Set the time zone
TIME_ZONE = 'Europe/Berlin'


# Enable localization for formats
USE_THOUSAND_SEPARATOR = True

# Set decimal and thousand separators for German format
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3  # Group digits into thousands


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-only-insecure-key-do-not-use-in-production'
    else:
        raise ValueError("SECRET_KEY environment variable is not set. Cannot start in production mode.")

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'bck-f86a70e697db.herokuapp.com,localhost,127.0.0.1'
).split(',')


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    # 'django_daisy',
    "django.contrib.admin",
    'django.contrib.humanize',  # Required for django-daisy
    'django_addanother',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    # 'django.contrib.sites',
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # external apps
    "rest_framework",
    "django_extensions",
    "widget_tweaks",
    'allauth',
    'allauth.account',


    # project apps
    "tracker",

    'django_quill',

]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]



ROOT_URLCONF = "finance_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'finance_project' / 'templates'],
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

WSGI_APPLICATION = "finance_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(
        default=None,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}
if not DATABASES["default"] and DEBUG:
    # Local dev fallback — set DATABASE_URL in .env instead
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "bck_2",
            "USER": "postgres",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization — German locale (consolidated, overrides boilerplate above)
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

AUTH_USER_MODEL = 'tracker.User'
LOGIN_REDIRECT_URL = 'log_create_compact'


JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-light",
    "accent": "accent-navy",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}


JAZZMIN_SETTINGS = {
    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "images/BCK-icon.svg",

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": "images/BCK_logo.png",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": "images/BCK-icon.svg",

    # Copyright on the footer
    "copyright": "BCK Architektur GMBH",


    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"name": "Back to App", "url": "/projects/", "new_window": False},
        {"model": "auth.user"}
    ],


    "show_ui_builder": False,

}


QUILL_CONFIGS = {
    'default': {
        'theme': 'snow',  # Available options: 'snow', 'bubble'
        'modules': {
            'toolbar': [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{'list': 'ordered'}, {'list': 'bullet'}],
                [{'indent': '-1'}, {'indent': '+1'}],
                [{'size': ['small', False, 'large', 'huge']}],
                [{'color': []}, {'background': []}],
                [{'align': []}],
                ['clean'],  # Remove formatting button
            ],
        },
    },
}


# ── Django REST Framework ───────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Return JSON only — no browsable HTML API in production
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
}

# ── Security Headers ────────────────────────────────────────────────────────────
# Heroku terminates SSL at its load balancer and forwards HTTP to dynos.
# SECURE_PROXY_SSL_HEADER tells Django to trust the X-Forwarded-Proto header
# so it knows the original request was HTTPS — without this, SECURE_SSL_REDIRECT
# causes an infinite redirect loop on Heroku.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'DENY'


# ── Logging ─────────────────────────────────────────────────────────────────────
# On Heroku the filesystem is ephemeral and logs/ does not exist — use console only.
# Locally, if logs/ exists, also write to a rotating file.
_LOG_DIR = BASE_DIR / 'logs'
_log_handlers = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}
_tracker_handlers = ['console']

if _LOG_DIR.exists():
    _log_handlers['file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': _LOG_DIR / 'django.log',
        'maxBytes': 5 * 1024 * 1024,  # 5 MB
        'backupCount': 5,
        'formatter': 'verbose',
    }
    _tracker_handlers.append('file')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': _log_handlers,
    'loggers': {
        'tracker': {
            'handlers': _tracker_handlers,
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
