import os
import dj_database_url
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Puxa a chave do arquivo oculto
SECRET_KEY = os.getenv('SECRET_KEY')
# SECRET_KEY = 'django-insecure-7y#wa%^t^14l$99d(f^3=rc(@b1)=#&u+1aeu4q33n7cn!5*c)'

# SECURITY WARNING: don't run with debug turned on in production!
# Converte a string 'True' do .env para um booleano verdadeiro; se não existir, será False por segurança
DEBUG = os.getenv('DEBUG') == 'True'
# Pega os endereços separados por vírgula no .env e transforma na lista exigida pelo Django
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


# Application definition

INSTALLED_APPS = [
    'jazzmin', # <-- Deve ser a PRIMEIRA linha
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'loteria',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <-- Adicione esta linha aqui
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


# settings.py

# A mágica acontece aqui: O Django vai procurar uma variável de nuvem chamada 'DATABASE_URL'.
# Se ele não encontrar (porque está no seu PC), ele usa o SQLite local tranquilamente.
# Se ele encontrar (quando estiver no Render), ele conecta no PostgreSQL corporativo!
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

# URL usada para acessar os arquivos (já deve existir)
STATIC_URL = '/static/'

# Diretório onde o Django vai reunir e guardar todos os arquivos estáticos durante a produção
import os # Garanta que o 'os' está importado no topo do arquivo
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Habilita a compressão agressiva e o controle de cache do WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

# Simulador de e-mail para ambiente de desenvolvimento (Padrão Django 6.0+)
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    }
}

# core/settings.py

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home' # <-- Altere de '/admin/' para 'home'

# Configurações do painel administrativo (Jazzmin)
JAZZMIN_SETTINGS = {
    "site_title": "Admin - Bolão Tracker",
    "site_header": "Bolão Tracker",
    # ... (suas outras configurações) ...
    "show_ui_builder": False,
    "custom_css": "css/admin_custom.css",
    "default_theme_mode": "dark", # <-- ADICIONE ESTA LINHA
}

# O segredo está aqui: usar o tema "default" com a navegação escura nativa
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "default_theme_mode": "dark",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}