from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t%8l!m^j)4kfiq0$wp0ck1-xj!f+bxr!s67ehys^1-+y785=g@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="sinevestback.onrender.com", cast=lambda v: [s.strip() for s in v.split(",")])

# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "drf_spectacular",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "rest_framework",
    "rest_framework_simplejwt",

    "authentication",
    "kyc",
    "wallet",
    "deposit",
    "transaction_pin",
    "withdrawal",
    "trade",
    "transaction_history",
    "user_profile",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_USER_MODEL = "authentication.User"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Sinevest Premium API",
    "DESCRIPTION": "Trading platform API — auth, KYC, wallet, deposits, withdrawals, trades, and transaction history.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("ACCESS_TOKEN_LIFETIME_MINUTES", default=60, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)),
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

OTP_EXPIRY_MINUTES = config("OTP_EXPIRY_MINUTES", default=10, cast=int)
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = config("PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", default=30, cast=int)
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")
MIN_DEPOSIT_AMOUNT = config("MIN_DEPOSIT_AMOUNT", default="10.00")
MIN_WITHDRAWAL_AMOUNT = config("MIN_WITHDRAWAL_AMOUNT", default="20.00")
PENDING_TRANSACTION_EXPIRY_MINUTES = config("PENDING_TRANSACTION_EXPIRY_MINUTES", default=5, cast=int)


# ─── JAZZMIN ──────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title":        "Sinevest Admin",
    "site_header":       "Sinevest",
    "site_brand":        "Sinevest",
    "welcome_sign":      "Welcome to Sinevest Control Panel",
    "copyright":         "Sinevest Inc.",
    "search_model":      ["accounts.User"],
    "topmenu_links": [
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Site",  "url": "/", "new_window": True},
        {"name": "Docs",  "url": "/swagger/", "new_window": True},
    ],
    "show_sidebar":         True,
    "navigation_expanded":  True,
    "icons": {
        "accounts":             "fas fa-users-cog",
        "accounts.User":        "fas fa-user",
        "accounts.OTPCode":     "fas fa-key",
        "wallet":               "fas fa-wallet",
        "investment":           "fas fa-chart-line",
        "management":           "fas fa-cogs",
        "auth.Group":           "fas fa-layer-group",
    },
    "default_icon_parents":  "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active":   True,
    "use_google_fonts_cdn":   True,
    "show_ui_builder":        False,
    "changeform_format":      "horizontal_tabs",
    "language_chooser":       False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":   False,
    "footer_small_text":   False,
    "body_small_text":     False,
    "brand_small_text":    False,
    "brand_colour":        "navbar-primary",
    "accent":              "accent-primary",
    "navbar":              "navbar-dark",
    "no_navbar_border":    False,
    "navbar_fixed":        True,
    "layout_boxed":        False,
    "footer_fixed":        False,
    "sidebar_fixed":       True,
    "sidebar":             "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand":  False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,
    "theme":               "default",
    "dark_mode_theme":     None,
    "button_classes": {
        "primary":  "btn-primary",
        "secondary":"btn-secondary",
        "info":     "btn-info",
        "warning":  "btn-warning",
        "danger":   "btn-danger",
        "success":  "btn-success",
    },
}