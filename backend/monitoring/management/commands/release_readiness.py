import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def enabled(name):
    return os.getenv(name, "False").strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Prüft sicherheits- und betriebsrelevante Voraussetzungen für einen öffentlichen Release."

    def handle(self, *args, **options):
        public_release = enabled("PUBLIC_RELEASE_ENABLED")
        domain = os.getenv("BAZKIT_DOMAIN", "").strip().lower()
        https_origin = f"https://{domain}" if domain else ""
        checks = [
            (not settings.DEBUG, "DJANGO_DEBUG muss False sein."),
            (
                (
                    settings.SECRET_KEY != "dev-only-secret-key"
                    and not settings.SECRET_KEY.startswith("django-insecure-")
                    and len(settings.SECRET_KEY) >= 50
                    and len(set(settings.SECRET_KEY)) >= 5
                ),
                "DJANGO_SECRET_KEY muss als langes Produktionsgeheimnis gesetzt sein.",
            ),
            (bool(settings.ALLOWED_HOSTS), "DJANGO_ALLOWED_HOSTS darf nicht leer sein."),
            ("*" not in settings.ALLOWED_HOSTS, "Wildcard-Hosts sind nicht erlaubt."),
            (bool(settings.EMAIL_HOST), "EMAIL_HOST fehlt."),
            (bool(settings.EMAIL_HOST_USER), "EMAIL_HOST_USER fehlt."),
            (bool(settings.EMAIL_HOST_PASSWORD), "EMAIL_HOST_PASSWORD fehlt."),
            (bool(settings.DEFAULT_FROM_EMAIL), "DEFAULT_FROM_EMAIL fehlt."),
            (bool(settings.CONTACT_EMAIL), "CONTACT_EMAIL fehlt."),
            (bool(settings.OPENAI_API_KEY), "OPENAI_API_KEY fehlt."),
            (bool(settings.ERROR_MONITORING_ENABLED), "ERROR_MONITORING_ENABLED muss aktiv sein."),
            (bool(settings.ERROR_ALERT_EMAIL), "ERROR_ALERT_EMAIL fehlt."),
        ]

        if public_release:
            valid_domain = bool(re.fullmatch(
                r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
                r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
                domain,
            ))
            checks.extend([
                (settings.HTTPS_ENABLED, "BAZKIT_HTTPS_ENABLED muss aktiv sein."),
                (settings.FRONTEND_URL.startswith("https://"), "FRONTEND_URL muss HTTPS verwenden."),
                (bool(domain), "BAZKIT_DOMAIN fehlt."),
                (valid_domain, "BAZKIT_DOMAIN ist kein gültiger öffentlicher Hostname."),
                (domain in settings.ALLOWED_HOSTS, "BAZKIT_DOMAIN fehlt in DJANGO_ALLOWED_HOSTS."),
                (https_origin in settings.CSRF_TRUSTED_ORIGINS, "Die HTTPS-Domain fehlt in DJANGO_CSRF_TRUSTED_ORIGINS."),
                (https_origin in settings.CORS_ALLOWED_ORIGINS, "Die HTTPS-Domain fehlt in DJANGO_CORS_ALLOWED_ORIGINS."),
                (settings.FRONTEND_URL.rstrip("/") == https_origin, "FRONTEND_URL und BAZKIT_DOMAIN stimmen nicht überein."),
                (settings.SESSION_COOKIE_SECURE, "Sichere Session-Cookies sind nicht aktiv."),
                (settings.CSRF_COOKIE_SECURE, "Sichere CSRF-Cookies sind nicht aktiv."),
                (settings.SECURE_HSTS_SECONDS > 0, "HSTS ist nicht aktiv."),
                (enabled("OFFSITE_BACKUP_ENABLED"), "OFFSITE_BACKUP_ENABLED muss aktiv sein."),
                (enabled("OFFSITE_BACKUP_REQUIRED"), "OFFSITE_BACKUP_REQUIRED muss aktiv sein."),
                (bool(os.getenv("R2_BACKUP_BUCKET_NAME", "").strip()), "R2_BACKUP_BUCKET_NAME fehlt."),
                (bool(os.getenv("R2_BUCKET_NAME", "").strip()), "R2_BUCKET_NAME für Bilder fehlt."),
                (bool(os.getenv("R2_ACCESS_KEY_ID", "").strip()), "R2_ACCESS_KEY_ID fehlt."),
                (bool(os.getenv("R2_SECRET_ACCESS_KEY", "").strip()), "R2_SECRET_ACCESS_KEY fehlt."),
                (bool(os.getenv("R2_ENDPOINT_URL", "").strip()), "R2_ENDPOINT_URL fehlt."),
            ])

        failures = [message for passed, message in checks if not passed]
        if failures:
            heading = (
                "Öffentlicher Release blockiert:"
                if public_release
                else "Vorbereitung noch unvollständig (PUBLIC_RELEASE_ENABLED=False):"
            )
            self.stdout.write(self.style.WARNING(heading))
            for failure in failures:
                self.stdout.write(f"- {failure}")
            if public_release:
                raise CommandError("Release-Readiness-Prüfung fehlgeschlagen.")
            return

        self.stdout.write(self.style.SUCCESS("Release-Readiness-Prüfung erfolgreich."))
