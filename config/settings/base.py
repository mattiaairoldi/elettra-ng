from pathlib import Path
import os

import environ


BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name, default=None)
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw_value = env(name, default=default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_optional(name: str, default: str = "") -> str | None:
    value = str(env(name, default=default)).strip()
    return value or None


SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "storages",
    "apps.common",
    "apps.identity",
    "apps.organizations",
    "apps.taxonomy",
    "apps.troubleshooting",
    "apps.cases",
    "apps.conversations",
    "apps.professionals",
    "apps.appointments",
    "apps.attachments",
    "apps.ai_assistant",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("POSTGRES_DB", default="elettra_ng"),
        "USER": env_optional("POSTGRES_USER"),
        "PASSWORD": env_optional("POSTGRES_PASSWORD"),
        "HOST": env_optional("POSTGRES_HOST"),
        "PORT": env_optional("POSTGRES_PORT"),
    }
}

AUTH_USER_MODEL = "identity.User"

LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
APP_BASE_URL = env("APP_BASE_URL", default="http://127.0.0.1:8000")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Elettra API V1",
    "DESCRIPTION": "API V1 schema for Elettra's modular backend.",
    "VERSION": "0.1.0",
    "ENUM_NAME_OVERRIDES": {
        "DiagnosticPublicationStatusEnum": [
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        "UserRoleEnum": [
            ("customer", "Customer"),
            ("professional", "Professional"),
            ("admin", "Admin"),
        ],
        "OrganizationMembershipRoleEnum": [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("administrative", "Administrative"),
            ("technician", "Technician"),
        ],
    },
}

REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/2")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = env_bool("CELERY_TASK_EAGER_PROPAGATES", True)

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", default="path")
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", default=None)
AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", True)
AWS_S3_FILE_OVERWRITE = env_bool("AWS_S3_FILE_OVERWRITE", False)

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_ALL_ORIGINS = False

SENTRY_DSN = env("SENTRY_DSN", default="")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="127.0.0.1")
EMAIL_PORT = env("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@local.test")
ORGANIZATION_INVITATION_TTL_DAYS = env.int("ORGANIZATION_INVITATION_TTL_DAYS", default=14)

AI_PROVIDER = env("AI_PROVIDER", default="local")
AI_DAILY_MESSAGE_LIMIT_PER_USER = env.int("AI_DAILY_MESSAGE_LIMIT_PER_USER", default=20)
AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT = env.int("AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT", default=4)
AI_CONTEXT_COMPACTION_MESSAGE_THRESHOLD = env.int("AI_CONTEXT_COMPACTION_MESSAGE_THRESHOLD", default=8)
AI_ESTIMATED_INPUT_COST_PER_1K_TOKENS = env.float("AI_ESTIMATED_INPUT_COST_PER_1K_TOKENS", default=0)
AI_ESTIMATED_OUTPUT_COST_PER_1K_TOKENS = env.float("AI_ESTIMATED_OUTPUT_COST_PER_1K_TOKENS", default=0)
AI_OPENAI_MODEL = env("AI_OPENAI_MODEL", default="gpt-5.4-mini")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_BASE_URL = env("OPENAI_BASE_URL", default="")
AI_STREAM_POLL_INTERVAL_SECONDS = env.float("AI_STREAM_POLL_INTERVAL_SECONDS", default=0.5)
AI_STREAM_TIMEOUT_SECONDS = env.float("AI_STREAM_TIMEOUT_SECONDS", default=30.0)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
