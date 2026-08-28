from collections import Counter

from django.core.management.base import BaseCommand

from products.catalog import canonical_recipe_name, recipe_ingredient_status
from products.ingredient_catalog import rebuild_product_aliases
from products.models import Product
from products.nutrition_quality import (
    NUTRIENT_FIELDS,
    apply_safe_zero_defaults,
    nutrition_is_complete,
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
        safely_completed = 0

        for product in products.iterator(chunk_size=500):
            canonical_name = canonical_recipe_name(
                product.name,
                product.source,
                product.external_id,
            )
            is_ingredient, reason = recipe_ingredient_status(
                product.name,
                product.category,
                product.source,
                product.external_id,
            )
            original_nutrients = {
                field: getattr(product, field)
                for field in NUTRIENT_FIELDS
            }
            nutrients = apply_safe_zero_defaults(
                product.name,
                product.source,
                product.external_id,
                original_nutrients,
            )
            complete_before = nutrition_is_complete(original_nutrients)
            complete = nutrition_is_complete(nutrients)
            if complete and not complete_before:
                safely_completed += 1
            if is_ingredient:
                eligible += 1
                canonical_counts[canonical_name.casefold()] += 1
                if not complete:
                    missing_nutrition += 1
            nutrients_changed = any(
                nutrients[field] != original_nutrients[field]
                for field in NUTRIENT_FIELDS
            )
            if (
                product.canonical_name != canonical_name
                or product.is_recipe_ingredient != is_ingredient
                or product.recipe_exclusion_reason != reason
                or nutrients_changed
            ):
                product.canonical_name = canonical_name
                product.is_recipe_ingredient = is_ingredient
                product.recipe_exclusion_reason = reason
                for field in NUTRIENT_FIELDS:
                    setattr(product, field, nutrients[field])
                pending.append(product)

        duplicate_groups = sum(1 for count in canonical_counts.values() if count > 1)
        self.stdout.write(
            f"Geprüft: {products.count()} Produkte · "
            f"Kochzutaten: {eligible} · "
            f"ohne vollständige Nährwerte: {missing_nutrition} · "
            f"mit sicheren Nullwerten vervollständigt: {safely_completed} · "
            f"zusammengeführte Namensgruppen: {duplicate_groups}"
        )
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Testlauf: Es wurde nichts geändert."))
            return

        if pending:
            Product.objects.bulk_update(
                pending,
                [
                    "canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason",
                    *NUTRIENT_FIELDS,
                ],
                batch_size=500,
            )
        rebuild_product_aliases(products)
        # Bereits gespeicherte Rezepte erhalten nach korrigierten BLS-Werten
        # sofort neue Summen. Nutzer müssen sie dafür nicht erst bearbeiten.
        from recipes.models import Recipe
        from recipes.serializers import calculate_recipe_nutrition

        recipes_recalculated = 0
        for recipe in Recipe.objects.prefetch_related("ingredients__product").iterator(
            chunk_size=200,
        ):
            calculate_recipe_nutrition(recipe, recipe.ingredients.all())
            recipes_recalculated += 1
        self.stdout.write(self.style.SUCCESS(
            "Zutatenkatalog und Synonyme wurden neu aufgebaut. Unvollständige "
            "Produkte bleiben gespeichert, werden aber in Rezepten nicht angeboten. "
            f"Nährwerte für {recipes_recalculated} gespeicherte Rezepte wurden neu berechnet."
        ))
