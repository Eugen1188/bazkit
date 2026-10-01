import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from products.models import Product
from users.email_verification import verification_url
from users.email_verification import password_reset_url
from users.models import User


class Command(BaseCommand):
    help = "Bereitet ausschließlich die isolierte Browser-Testdatenbank vor."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["reset", "create-user", "verification-url", "password-reset-url", "seed-product", "user-exists"])
        parser.add_argument("--email", default="")
        parser.add_argument("--password", default="E2ePasswort123")
        parser.add_argument("--first-name", default="E2E")
        parser.add_argument("--last-name", default="Nutzer")

    def handle(self, *args, **options):
        if not getattr(settings, "E2E_TESTING_ENABLED", False):
            raise CommandError("Dieser Befehl darf nur mit config.e2e_settings laufen.")

        action = options["action"]
        email = options["email"].strip().lower()
        if action == "reset":
            User.objects.all().delete()
            Product.objects.all().delete()
            image_directory = getattr(settings, "E2E_IMAGE_STORAGE_DIRECTORY", None)
            if image_directory:
                shutil.rmtree(image_directory, ignore_errors=True)
            self.stdout.write("reset")
            return

        if action == "seed-product":
            product, _created = Product.objects.update_or_create(
                source="curated",
                external_id="e2e-kartoffel",
                defaults={
                    "name": "Kartoffel",
                    "canonical_name": "Kartoffel",
                    "is_recipe_ingredient": True,
                    "catalog_status": "approved",
                    "default_unit": "g",
                    "calories_per_100g": 77,
                    "protein_per_100g": 2,
                    "carbohydrates_per_100g": 17,
                    "fat_per_100g": 0.1,
                    "fiber_per_100g": 2.2,
                },
            )
            self.stdout.write(str(product.pk))
            return

        if not email:
            raise CommandError("--email ist erforderlich.")

        if action == "create-user":
            user, _created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": options["first_name"],
                    "last_name": options["last_name"],
                    "is_active": True,
                    "email_verified_at": timezone.now(),
                    "terms_accepted_at": timezone.now(),
                    "terms_version": settings.LEGAL_TERMS_VERSION,
                },
            )
            user.username = email
            user.is_active = True
            user.set_password(options["password"])
            user.save()
            self.stdout.write(str(user.pk))
            return

        user = User.objects.filter(email__iexact=email).first()
        if action == "user-exists":
            self.stdout.write("true" if user else "false")
            return
        if action == "password-reset-url":
            if user is None or not user.is_active:
                raise CommandError("Kein aktives Konto gefunden.")
            self.stdout.write(password_reset_url(user))
            return
        if user is None or user.email_verification_token is None:
            raise CommandError("Kein unbestätigtes Konto mit Token gefunden.")
        self.stdout.write(verification_url(user.email_verification_token))
