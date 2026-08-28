from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Q

from products.ingredient_catalog import INGREDIENT_DEFINITIONS
from products.models import Product, ProductAlias
from products.nutrition_quality import NUTRIENT_FIELDS


class Command(BaseCommand):
    help = "Prüft Suchbegriffe, Nährwerte, Kategorien und Vorratskennzeichen des Zutatenkatalogs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--show-missing",
            action="store_true",
            help="Listet rezeptfähige Produkte mit fehlenden Kernnährwerten auf.",
        )

    def handle(self, *args, **options):
        products = Product.objects.all()
        eligible = products.filter(is_recipe_ingredient=True)
        missing_nutrition = Q()
        for field in NUTRIENT_FIELDS:
            missing_nutrition |= Q(**{f"{field}__isnull": True})
        incomplete = eligible.filter(missing_nutrition)
        complete_count = eligible.count() - incomplete.count()
        categories = Counter(
            eligible.values_list("shopping_category", flat=True)
        )
        curated_alias_count = sum(
            len({definition.canonical_name, *definition.aliases})
            for definition in INGREDIENT_DEFINITIONS
        )

        self.stdout.write("ZUTATENKATALOG-AUDIT")
        self.stdout.write(f"Produkte insgesamt: {products.count()}")
        self.stdout.write(f"Als Kochzutat klassifiziert: {eligible.count()}")
        self.stdout.write(f"Davon mit vollständigen Kernnährwerten: {complete_count}")
        self.stdout.write(f"Davon mit Nährwertlücken: {incomplete.count()}")
        self.stdout.write(f"Gespeicherte Suchaliasse: {ProductAlias.objects.count()}")
        self.stdout.write(f"Redaktionell definierte Begriffe: {len(INGREDIENT_DEFINITIONS)}")
        self.stdout.write(f"Redaktionell definierte Schreibweisen/Synonyme: {curated_alias_count}")
        self.stdout.write(
            f"Als typische Vorratszutat markiert: {eligible.filter(is_common_pantry=True).count()}"
        )
        self.stdout.write("Einkaufskategorien:")
        for category, count in sorted(categories.items()):
            self.stdout.write(f"  {category or 'leer'}: {count}")

        if options["show_missing"] and incomplete.exists():
            self.stdout.write("Produkte mit fehlenden Kernnährwerten:")
            for product in incomplete.order_by("canonical_name", "name"):
                missing = [
                    field.replace("_per_100g", "")
                    for field in NUTRIENT_FIELDS
                    if getattr(product, field) is None
                ]
                self.stdout.write(
                    f"  {product.source}:{product.external_id} · "
                    f"{product.canonical_name or product.name} · fehlt: {', '.join(missing)}"
                )

        if incomplete.exists():
            self.stdout.write(self.style.WARNING(
                "Produkte mit Lücken bleiben aus der Rezeptsuche ausgeschlossen."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Alle angebotenen Rezeptzutaten besitzen vollständige Kernnährwerte."
            ))
