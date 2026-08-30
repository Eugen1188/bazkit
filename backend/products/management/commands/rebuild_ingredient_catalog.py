from collections import Counter
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from products.catalog import (
    CURATED_CONVERSION_SOURCE,
    canonical_recipe_name,
    curated_unit_conversions,
    recipe_ingredient_status,
    suggested_unit_for_product,
)
from products.curated import ensure_curated_ingredients
from products.ingredient_catalog import definition_for_product, rebuild_product_aliases
from products.models import Product, ProductUnitConversion
from products.nutrition_quality import (
    NUTRIENT_FIELDS,
    apply_safe_zero_defaults,
    nutrition_is_complete,
)
from products.shopping_taxonomy import infer_product_taxonomy


class Command(BaseCommand):
    help = "Baut kanonische Zutatennamen und Synonyme neu auf und prüft die Nährwertabdeckung."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if not options["dry_run"]:
            ensure_curated_ingredients()
        products = Product.objects.filter(source__in=("bls", "open_food_facts", "usda"))
        pending = []
        missing_nutrition = 0
        eligible = 0
        canonical_counts = Counter()
        safely_completed = 0
        managed_conversions = {}

        for product in products.iterator(chunk_size=500):
            canonical_name = canonical_recipe_name(
                product.name,
                product.source,
                product.external_id,
            )
            definition = definition_for_product(
                product.source,
                product.external_id,
                canonical_name,
            )
            is_ingredient, reason = recipe_ingredient_status(
                product.name,
                product.category,
                product.source,
                product.external_id,
            )
            shopping_category, is_common_pantry = infer_product_taxonomy(
                product.name,
                canonical_name,
                product.category,
                product.source,
                product.external_id,
            )
            default_unit = suggested_unit_for_product(
                product.name, canonical_name, shopping_category, product.default_unit,
            ) if definition is not None else (
                product.default_unit or ("ml" if shopping_category == "drinks" else "g")
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
                or product.shopping_category != shopping_category
                or product.is_common_pantry != is_common_pantry
                or product.default_unit != default_unit
                or nutrients_changed
            ):
                product.canonical_name = canonical_name
                product.is_recipe_ingredient = is_ingredient
                product.recipe_exclusion_reason = reason
                product.shopping_category = shopping_category
                product.is_common_pantry = is_common_pantry
                product.default_unit = default_unit
                for field in NUTRIENT_FIELDS:
                    setattr(product, field, nutrients[field])
                pending.append(product)

            conversions = (
                curated_unit_conversions(definition.canonical_name)
                if definition is not None else []
            )
            package_factor = {
                "mg": Decimal("0.001"), "g": Decimal("1"),
                "kg": Decimal("1000"), "ml": Decimal("1"),
                "cl": Decimal("10"), "dl": Decimal("100"),
                "l": Decimal("1000"),
            }.get(str(product.package_unit or "").casefold())
            try:
                package_amount = (
                    Decimal(str(product.package_quantity))
                    if product.package_quantity is not None else None
                )
            except (InvalidOperation, TypeError, ValueError):
                package_amount = None
            if package_amount and package_amount > 0 and package_factor is not None:
                package_label = next(
                    (
                        label for label in ("Dose", "Glas", "Becher")
                        if label.casefold() in str(product.name or "").casefold()
                    ),
                    "Packung",
                )
                conversions = [
                    conversion for conversion in conversions
                    if conversion["unit"] != package_label
                ]
                conversions.append({
                    "unit": package_label,
                    "grams_per_unit": package_amount * package_factor,
                    "source": "Open Food Facts Packungsangabe",
                    "confidence": "verified",
                })
            for conversion in conversions:
                managed_conversions[(product.id, conversion["unit"])] = ProductUnitConversion(
                    product_id=product.id,
                    unit=conversion["unit"],
                    grams_per_unit=conversion["grams_per_unit"],
                    source=conversion["source"],
                    confidence=conversion["confidence"],
                    is_active=True,
                )

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
                    "shopping_category", "is_common_pantry",
                    "default_unit",
                    *NUTRIENT_FIELDS,
                ],
                batch_size=500,
            )
        self.stdout.write("Produktdaten aktualisiert. Küchenumrechnungen werden synchronisiert …")
        self.stdout.flush()
        conversion_rows = list(managed_conversions.values())
        with transaction.atomic():
            ProductUnitConversion.objects.filter(
                product__source__in=("bls", "open_food_facts", "usda"),
                source__in=(CURATED_CONVERSION_SOURCE, "Open Food Facts Packungsangabe"),
            ).delete()
            if conversion_rows:
                ProductUnitConversion.objects.bulk_create(
                    conversion_rows,
                    batch_size=1000,
                    update_conflicts=True,
                    update_fields=[
                        "grams_per_unit", "source", "confidence", "is_active",
                    ],
                    unique_fields=["product", "unit"],
                )
        conversions_synced = len({row.product_id for row in conversion_rows})
        self.stdout.write(
            f"Küchenumrechnungen für {conversions_synced} Produkte synchronisiert. "
            "Suchbegriffe werden neu aufgebaut …"
        )
        self.stdout.flush()
        rebuild_product_aliases(products)
        self.stdout.write("Suchbegriffe aktualisiert. Rezeptnährwerte werden neu berechnet …")
        self.stdout.flush()
        # Bereits gespeicherte Rezepte erhalten nach korrigierten BLS-Werten
        # sofort neue Summen. Nutzer müssen sie dafür nicht erst bearbeiten.
        from recipes.models import Recipe
        from recipes.serializers import calculate_recipe_nutrition

        recipes_recalculated = 0
        for recipe in Recipe.objects.prefetch_related(
            "ingredients__product__unit_conversions",
        ).iterator(
            chunk_size=200,
        ):
            calculate_recipe_nutrition(recipe, recipe.ingredients.all())
            recipes_recalculated += 1
        self.stdout.write(self.style.SUCCESS(
            "Zutatenkatalog und Synonyme wurden neu aufgebaut. Unvollständige "
            "Produkte bleiben gespeichert, werden aber in Rezepten nicht angeboten. "
            f"Küchenumrechnungen für {conversions_synced} Produkte synchronisiert. "
            f"Nährwerte für {recipes_recalculated} gespeicherte Rezepte wurden neu berechnet."
        ))
