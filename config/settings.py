import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Paths ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security & Debug ───────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key-for-dev')
DEBUG = False

# ── Allowed Hosts ─────────────────────
# Base production domains always included.
# Both Railway auto domains are listed explicitly so the app is reachable
# via the Railway-provided URL while DNS propagation completes for the
# custom domain.
_DEFAULT_HOSTS = (
    'www.practicalkhata.pro.bd,'
    'practicalkhata.pro.bd,'
    'practical-khata-production.up.railway.app,'
    'practical-khata-production-67ea.up.railway.app,'
    'localhost,'
    '127.0.0.1'
)
_allowed = os.getenv('ALLOWED_HOSTS', _DEFAULT_HOSTS).split(',')

# Also include any Railway-provided public domain set via environment variable
# (covers future domain changes without requiring a code update).
_railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain and _railway_domain not in _allowed:
    _allowed.append(_railway_domain)

ALLOWED_HOSTS = [h.strip() for h in _allowed if h.strip()]


# ── Installed Apps ─────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

# ── Middleware ────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── URL Config ───────────────────────
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ── Templates ─────────────────────────
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
                'core.context_processors.cart_count',
            ],
        },
    },
]

# ── Database ──────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Static & Media ────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Defaults ─────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# ── AI Keys ───────────────────────────
OPENAI_API_KEY      = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL        = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
# Do NOT hardcode API keys in source. Prefer environment variables.
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
HUGGINGFACE_MODEL   = os.getenv('HUGGINGFACE_MODEL', 'google/flan-t5-small')