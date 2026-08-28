from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from products.catalog import recipe_ingredient_status
from products.ingredient_catalog import INGREDIENT_DEFINITIONS, normalize_alias
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
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Bricht bei Kataloglücken ab und eignet sich damit für Deployment/CI.",
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
        searchable = eligible.exclude(missing_nutrition)

        alias_owners = defaultdict(set)
        for definition in INGREDIENT_DEFINITIONS:
            for alias in (definition.canonical_name, *definition.aliases):
                alias_owners[normalize_alias(alias)].add(definition.canonical_name)
        alias_conflicts = {
            alias: names for alias, names in alias_owners.items() if len(names) > 1
        }

        available_keys = set(searchable.values_list("source", "external_id"))
        unresolved_definitions = []
        definitions_without_source = []
        for definition in INGREDIENT_DEFINITIONS:
            keys = {
                *(("bls", code) for code in definition.preferred_bls_codes),
                *(("usda", external_id) for external_id in definition.preferred_usda_ids),
            }
            if not keys:
                definitions_without_source.append(definition.canonical_name)
            elif not keys.intersection(available_keys):
                unresolved_definitions.append(definition.canonical_name)

        uncategorized = searchable.filter(shopping_category="other")
        stale_prepared_products = []
        for product in searchable.iterator(chunk_size=500):
            if not recipe_ingredient_status(
                product.name,
                product.category,
                product.source,
                product.external_id,
            )[0]:
                stale_prepared_products.append(product)

        self.stdout.write("ZUTATENKATALOG-AUDIT")
        self.stdout.write(f"Produkte insgesamt: {products.count()}")
        self.stdout.write(f"Als Kochzutat klassifiziert: {eligible.count()}")
        self.stdout.write(f"Davon mit vollständigen Kernnährwerten: {complete_count}")
        self.stdout.write(f"Davon mit Nährwertlücken: {incomplete.count()}")
        self.stdout.write(f"Gespeicherte Suchaliasse: {ProductAlias.objects.count()}")
        self.stdout.write(f"Redaktionell definierte Begriffe: {len(INGREDIENT_DEFINITIONS)}")
        self.stdout.write(f"Redaktionell definierte Schreibweisen/Synonyme: {curated_alias_count}")
        self.stdout.write(f"Nicht auflösbare redaktionelle Zutaten: {len(unresolved_definitions)}")
        self.stdout.write(f"Definitionen ohne geprüfte Nährwertquelle: {len(definitions_without_source)}")
        self.stdout.write(f"Mehrdeutige Synonyme: {len(alias_conflicts)}")
        self.stdout.write(f"Suchbare Zutaten ohne Einkaufskategorie: {uncategorized.count()}")
        self.stdout.write(f"Veraltete Fertiggericht-Freigaben: {len(stale_prepared_products)}")
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

        strict_errors = []
        if definitions_without_source:
            strict_errors.append(
                "Definitionen ohne Quelle: " + ", ".join(definitions_without_source[:20])
            )
        if unresolved_definitions:
            strict_errors.append(
                "Nicht auflösbare Zutaten: " + ", ".join(unresolved_definitions[:20])
            )
        if alias_conflicts:
            formatted = [
                f"{alias} → {', '.join(sorted(names))}"
                for alias, names in sorted(alias_conflicts.items())
            ]
            strict_errors.append("Mehrdeutige Synonyme: " + "; ".join(formatted[:20]))
        if uncategorized.exists():
            strict_errors.append(
                "Suchbare Zutaten ohne Kategorie: "
                + ", ".join(uncategorized.values_list("name", flat=True)[:20])
            )
        if stale_prepared_products:
            strict_errors.append(
                "Fertiggerichte fälschlich suchbar: "
                + ", ".join(product.name for product in stale_prepared_products[:20])
            )

        if options["strict"] and strict_errors:
            raise CommandError(" | ".join(strict_errors))
        if options["strict"]:
            self.stdout.write(self.style.SUCCESS(
                "Strenge Katalogprüfung bestanden: jede definierte Zutat ist eindeutig, "
                "kategorisiert und mit vollständigen Nährwerten verfügbar."
            ))
