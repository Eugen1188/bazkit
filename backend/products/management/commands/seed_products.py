import json
from pathlib import Path

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = "Importiert alle Produktdateien aus products/data."

    def handle(self, *args, **options):

        data_directory = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "data"
        )

        if not data_directory.exists():
            self.stderr.write(
                self.style.ERROR(
                    f"Ordner nicht gefunden: {data_directory}"
                )
            )
            return

        json_files = sorted(
            data_directory.glob("*.json")
        )

        if not json_files:
            self.stderr.write(
                self.style.ERROR(
                    "Keine JSON-Dateien gefunden."
                )
            )
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for file_path in json_files:

            self.stdout.write(
                f"Lade {file_path.name} ..."
            )

            try:
                with file_path.open(
                    "r",
                    encoding="utf-8-sig"
                ) as file:
                    products = json.load(file)

            except (
                json.JSONDecodeError,
                OSError
            ) as error:

                self.stderr.write(
                    self.style.ERROR(
                        f"Fehler in {file_path.name}: {error}"
                    )
                )

                continue

            if not isinstance(
                products,
                list
            ):
                continue

            for product_data in products:

                name = (
                    product_data
                    .get(
                        "name",
                        ""
                    )
                    .strip()
                )

                category = (
                    product_data
                    .get(
                        "category",
                        ""
                    )
                    .strip()
                )

                default_unit = (
                    product_data
                    .get(
                        "default_unit",
                        ""
                    )
                    .strip()
                )

                if not name:
                    skipped_count += 1
                    continue

                existing_product = (
                    Product.objects
                    .filter(
                        name__iexact=name
                    )
                    .first()
                )

                if existing_product:

                    changed = False

                    if (
                        category
                        and
                        existing_product.category
                        != category
                    ):
                        existing_product.category = (
                            category
                        )

                        changed = True

                    if (
                        default_unit
                        and
                        existing_product.default_unit
                        != default_unit
                    ):
                        existing_product.default_unit = (
                            default_unit
                        )

                        changed = True

                    if changed:
                        existing_product.save()

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
                "\nImport abgeschlossen:\n"
                f"{created_count} erstellt\n"
                f"{updated_count} aktualisiert\n"
                f"{skipped_count} übersprungen"
            )
        )