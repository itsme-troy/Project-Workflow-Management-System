from pathlib import Path
import os 
from pyngrok import ngrok  # Import Ngrok


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-dnm=7q)@1=$9+8g^@m(i*@--6$2@)*7%egj0cg2w^uv8foy3nc"

DEBUG = True  # Change to False for production

# ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok.app",
]

# Dynamically add the Ngrok URL to ALLOWED_HOSTS
if os.getenv("RUN_MAIN", None) != "true":  # Prevent duplicate Ngrok connections
    public_url = ngrok.connect(8000).public_url  # Replace 8000 with your Django server port
    print(f"Ngrok URL: {public_url}")
    ALLOWED_HOSTS.append(public_url.replace("https://", "").replace("http://", ""))


ABSTRACT_API_KEY = "27979452bb704be3a9fcdcaf1d5ab7b6"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "project",
    "users",
    "mutual_availability",
    "free_schedule", 
    'defense_schedule',
    # "common_schedule", 
    "google_calendar",
    # "calendarapp.apps.CalendarappConfig",
    'rest_framework',
    'channels',
    'corsheaders',
 
]

# Specify the ASGI application (for Django Channels)
ASGI_APPLICATION = 'yourproject.asgi.application'

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = "cms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "cms.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "cms",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "USER": "root",
        "PASSWORD": "root",
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
# STATICFILES_DIRS = [ os.path.join(BASE_DIR,'static') ]
STATICFILES_DIRS = [
    BASE_DIR / "project/static",  # Adjust this line if necessary
    BASE_DIR / "free_schedule/static",
    BASE_DIR / "mutual_availability/static",
]
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# User Model
AUTH_USER_MODEL = "project.AppUser"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = "email"

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'lteodoro@gbox.adnu.edu.ph'
EMAIL_HOST_PASSWORD = 'akiutvbdldgwgxos'  # Use app-specific password for Gmail
DEFAULT_FROM_EMAIL = 'lteodoro@gbox.adnu.edu.ph'
EMAIL_USE_TLS = True

PASSWORD_RESET_TIMEOUT = 14400



CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
AUTHENTICATION_BACKENDS = [
    'users.authentication.EmailVerifiedBackend',  
    'django.contrib.auth.backends.ModelBackend',
]
