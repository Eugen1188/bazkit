from collections import Counter

from django.core.management.base import BaseCommand

from products.catalog import canonical_recipe_name, recipe_ingredient_status
from products.ingredient_catalog import rebuild_product_aliases
from products.models import Product


NUTRIENT_FIELDS = (
    "calories_per_100g",
    "protein_per_100g",
    "carbohydrates_per_100g",
    "fat_per_100g",
    "fiber_per_100g",
)


class Command(BaseCommand):
    help = "Baut kanonische Zutatennamen und Synonyme neu auf und prüft die Nährwertabdeckung."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        products = Product.objects.filter(source__in=("bls", "open_food_facts", "usda"))
        pending = []
        missing_nutrition = 0
        eligible = 0
        canonical_counts = Counter()

        for product in products.iterator(chunk_size=500):
            canonical_name = canonical_recipe_name(product.name)
            is_ingredient, reason = recipe_ingredient_status(
                product.name,
                product.category,
                product.source,
                product.external_id,
            )
            complete = all(getattr(product, field) is not None for field in NUTRIENT_FIELDS)
            if is_ingredient:
                eligible += 1
                canonical_counts[canonical_name.casefold()] += 1
                if not complete:
                    missing_nutrition += 1
            if (
                product.canonical_name != canonical_name
                or product.is_recipe_ingredient != is_ingredient
                or product.recipe_exclusion_reason != reason
            ):
                product.canonical_name = canonical_name
                product.is_recipe_ingredient = is_ingredient
                product.recipe_exclusion_reason = reason
                pending.append(product)

        duplicate_groups = sum(1 for count in canonical_counts.values() if count > 1)
        self.stdout.write(
            f"Geprüft: {products.count()} Produkte · "
            f"Kochzutaten: {eligible} · "
            f"ohne vollständige Nährwerte: {missing_nutrition} · "
            f"zusammengeführte Namensgruppen: {duplicate_groups}"
        )
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Testlauf: Es wurde nichts geändert."))
            return

        if pending:
            Product.objects.bulk_update(
                pending,
                ["canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason"],
                batch_size=500,
            )
        rebuild_product_aliases(products)
        self.stdout.write(self.style.SUCCESS(
            "Zutatenkatalog und Synonyme wurden neu aufgebaut. Unvollständige "
            "Produkte bleiben gespeichert, werden aber in Rezepten nicht angeboten."
        ))
