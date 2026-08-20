import json
from pathlib import Path

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = "Importiert Standardprodukte in die Product-Tabelle."

    def handle(self, *args, **options):

        file_path = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "data"
            / "products.json"
        )

        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    f"Datei nicht gefunden: {file_path}"
                )
            )
            return

        with file_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            products = json.load(file)

        created_count = 0
        updated_count = 0

        for product_data in products:

            name = (
                product_data
                .get("name", "")
                .strip()
            )

            category = (
                product_data
                .get("category", "")
                .strip()
            )

            default_unit = (
                product_data
                .get("default_unit", "")
                .strip()
            )

            if not name:
                continue

            product = (
                Product.objects
                .filter(
                    name__iexact=name
                )
                .first()
            )

            if product:
                changed = False

                if (
                    category
                    and
                    product.category != category
                ):
                    product.category = category
                    changed = True

                if (
                    default_unit
                    and
                    product.default_unit != default_unit
                ):
                    product.default_unit = default_unit
                    changed = True

                if changed:
                    product.save()
                    updated_count += 1

                continue

            Product.objects.create(
                name=name,
                category=category,
                default_unit=default_unit
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} Produkte erstellt, "
                f"{updated_count} aktualisiert."
            )
        )