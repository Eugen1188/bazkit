from pathlib import Path

from .test_settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "e2e.sqlite3",  # noqa: F405
        "OPTIONS": {"timeout": 20},
    }
}

E2E_TESTING_ENABLED = True
E2E_IMAGE_STORAGE_DIRECTORY = BASE_DIR / ".e2e-images"  # noqa: F405
FRONTEND_URL = "http://127.0.0.1:14200"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CORS_ALLOWED_ORIGINS = ["http://localhost:14200", "http://127.0.0.1:14200"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:14200", "http://127.0.0.1:14200"]
