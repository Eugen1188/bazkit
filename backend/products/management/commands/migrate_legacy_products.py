from django.core.management.base import BaseCommand
from django.db import transaction

from lists.models import SavedListItem, ShoppingListItem
from products.legacy_normalization import parse_legacy_product_name
from products.models import Product
from recipes.models import Ingredients


class Command(BaseCommand):
    help = (
        "Analysiert alte lokale Products und löst ihre Verknüpfungen sicher in "
        "freie Listen-/Rezeptnamen auf. Ohne --apply ist der Befehl ein Dry-Run."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--limit", type=int)

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        products = Product.objects.filter(source__isnull=True).order_by("id")
        if options.get("limit"):
            products = products[: options["limit"]]

        report = {
            "products": 0,
            "names_with_package": 0,
            "shopping_items_preserved": 0,
            "saved_items_preserved": 0,
            "recipe_ingredients_preserved": 0,
        }

        with transaction.atomic():
            for product in products.iterator():
                report["products"] += 1
                parsed = parse_legacy_product_name(product.name)
                if parsed.package_quantity is not None:
                    report["names_with_package"] += 1

                relations = (
                    (ShoppingListItem, "shopping_items_preserved"),
                    (SavedListItem, "saved_items_preserved"),
                    (Ingredients, "recipe_ingredients_preserved"),
                )
                for model, counter in relations:
                    queryset = model.objects.filter(product=product)
                    count = queryset.count()
                    report[counter] += count
                    if not apply_changes or not count:
                        continue
                    for item in queryset.iterator():
                        item.product = None
                        item.name = parsed.normalized_name[:100]
                        # Eine erkannte Endmenge ist eine Packungsgröße. Bestehende
                        # gewünschte Mengen werden daher niemals überschrieben.
                        if hasattr(item, "package_quantity") and parsed.package_quantity is not None:
                            item.package_quantity = parsed.package_quantity
                            item.package_unit = parsed.package_unit
                            if item.quantity is None and parsed.package_count > 1:
                                item.quantity = parsed.package_count
                                item.unit = "Packung"
                        item.save()

            if not apply_changes:
                transaction.set_rollback(True)

        mode = "APPLY" if apply_changes else "DRY-RUN"
        self.stdout.write(self.style.SUCCESS(f"Legacy migration {mode}"))
        for key, value in report.items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(
            "Alte Products wurden nicht gelöscht. Nach Prüfung können unreferenzierte "
            "Datensätze separat archiviert werden."
        )
