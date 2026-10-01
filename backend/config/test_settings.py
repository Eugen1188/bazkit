from .settings import *  # noqa: F403


SECRET_KEY = "bazkit-tests-only-9vQ3!mL8#rT2@xP7$kN4-wF6_yH1+cD5"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

COMMUNITY_THROTTLES_ENABLED = False
AUTH_THROTTLES_ENABLED = False
HTTPS_ENABLED = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
ERROR_MONITORING_ENABLED = False
