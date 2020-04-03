import ldap

from django_auth_ldap.config import LDAPGroupQuery, LDAPSearch, PosixGroupType

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["etatcivil.kdl.kcl.ac.uk"])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"] = env.db("DATABASE_URL")  # noqa F405
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)

# STATIC
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# MEDIA
# ------------------------------------------------------------------------------

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="Etat Civil <noreply@kcl.ac.uk>"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[Etat Civil]")

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Anymail (Mailgun)
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
INSTALLED_APPS += ["anymail"]  # noqa F405
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_DOMAIN"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL", default="https://api.mailgun.net/v3"),
}


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}
# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    # https://django-auth-ldap.readthedocs.io/
    "django_auth_ldap.backend.LDAPBackend"
] + AUTHENTICATION_BACKENDS  # noqa

# LDAP AUTHENTICATION
# ------------------------------------------------------------------------------
# https://django-auth-ldap.readthedocs.io/
LDAP_BASE_DC = env("LDAP_BASE_DC")
LDAP_BASE_OU = f"ou=groups,{LDAP_BASE_DC}"
LDAP_BASE_GROUP = f"cn={env('LDAP_BASE_GROUP')},{LDAP_BASE_OU}"
LDAP_PROJECT_GROUP = f"cn=etatcivil,{LDAP_BASE_OU}"

# Baseline configuration
AUTH_LDAP_SERVER_URI = env("LDAP_SERVER_URI")
AUTH_LDAP_BIND_DN = env("LDAP_BIND_DN", default="")
AUTH_LDAP_BIND_PASSWORD = env("LDAP_BIND_PASSWORD", default="")
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=people," + LDAP_BASE_DC

# Set up the basic group parameters
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    LDAP_BASE_OU, ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)"
)
AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")

# Simple group restrictions
AUTH_LDAP_REQUIRE_GROUP = LDAPGroupQuery(LDAP_BASE_GROUP) | LDAPGroupQuery(
    LDAP_PROJECT_GROUP
)

# Populate the Django user from the LDAP directory
AUTH_LDAP_ALWAYS_UPDATE_USER = False

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": env("LDAP_FIRST_NAME_FIELD"),
    "last_name": env("LDAP_LAST_NAME_FIELD"),
    "email": env("LDAP_EMAIL_FIELD"),
}

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": LDAPGroupQuery(LDAP_BASE_GROUP) | LDAPGroupQuery(LDAP_PROJECT_GROUP),
    "is_staff": LDAPGroupQuery(LDAP_BASE_GROUP) | LDAPGroupQuery(LDAP_PROJECT_GROUP),
    "is_superuser": LDAP_BASE_GROUP,
    # TODO: Wagtail group settings
}

# Your stuff...
# ------------------------------------------------------------------------------
