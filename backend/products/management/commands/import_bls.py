import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree

from django.core.management.base import BaseCommand, CommandError

from products.models import Product
from products.catalog import (
    canonical_recipe_name,
    recipe_ingredient_status,
    suggested_unit_for_product,
)
from products.curated import ensure_curated_ingredients
from products.ingredient_catalog import rebuild_product_aliases
from products.nutrition_quality import apply_safe_zero_defaults
from products.shopping_taxonomy import infer_product_taxonomy


CELL_REFERENCE = re.compile(r"([A-Z]+)\d+")
WANTED_HEADERS = {
    "external_id": "BLS Code",
    "name": "Lebensmittelbezeichnung",
    "calories_per_100g": "ENERCC ",
    "protein_per_100g": "PROT625 ",
    "fat_per_100g": "FAT ",
    "carbohydrates_per_100g": "CHO ",
    "fiber_per_100g": "FIBT ",
}


def column_number(reference):
    match = CELL_REFERENCE.match(reference or "")
    if not match:
        return None
    number = 0
    for character in match.group(1):
        number = number * 26 + ord(character) - 64
    return number


def decimal_or_none(value):
    if value in (None, "", "-"):
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None


class XlsxRows:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

    def __init__(self, path):
        self.archive = zipfile.ZipFile(path)
        self.shared_strings = self._shared_strings()

    def _shared_strings(self):
        try:
            source = self.archive.open("xl/sharedStrings.xml")
        except KeyError:
            return []
        strings = []
        for event, element in ElementTree.iterparse(source, events=("end",)):
            if element.tag == f"{self.namespace}si":
                strings.append("".join(node.text or "" for node in element.iter(f"{self.namespace}t")))
                element.clear()
        return strings

    def __iter__(self):
        source = self.archive.open("xl/worksheets/sheet1.xml")
        for event, row in ElementTree.iterparse(source, events=("end",)):
            if row.tag != f"{self.namespace}row":
                continue
            values = {}
            for cell in row.findall(f"{self.namespace}c"):
                column = column_number(cell.attrib.get("r"))
                value_node = cell.find(f"{self.namespace}v")
                if column is None or value_node is None:
                    continue
                value = value_node.text
                if cell.attrib.get("t") == "s" and value is not None:
                    value = self.shared_strings[int(value)]
                values[column] = value
            row.clear()
            yield values

    def close(self):
        self.archive.close()


class Command(BaseCommand):
    help = "Importiert den offiziellen BLS 4.0 aus der deutschen XLSX-Datei."

    def add_arguments(self, parser):
        parser.add_argument("xlsx", type=Path)
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = options["xlsx"]
        if not path.is_file():
            raise CommandError(f"Datei nicht gefunden: {path}")
        rows = XlsxRows(path)
        iterator = iter(rows)
        try:
            headers = next(iterator)
            columns = {}
            for field, prefix in WANTED_HEADERS.items():
                columns[field] = next((column for column, header in headers.items() if str(header).startswith(prefix)), None)
            missing = [field for field, column in columns.items() if column is None]
            if missing:
                raise CommandError(f"BLS-Spalten fehlen: {', '.join(missing)}")
            products = []
            for row in iterator:
                external_id = str(row.get(columns["external_id"], "")).strip()
                name = re.sub(r"\s+", " ", str(row.get(columns["name"], ""))).strip()
                if not external_id or not name:
                    continue
                is_recipe_ingredient, exclusion_reason = recipe_ingredient_status(
                    name,
                    source="bls",
                    external_id=external_id,
                )
                nutrients = apply_safe_zero_defaults(
                    name,
                    "bls",
                    external_id,
                    {
                        "calories_per_100g": decimal_or_none(row.get(columns["calories_per_100g"])),
                        "protein_per_100g": decimal_or_none(row.get(columns["protein_per_100g"])),
                        "carbohydrates_per_100g": decimal_or_none(row.get(columns["carbohydrates_per_100g"])),
                        "fat_per_100g": decimal_or_none(row.get(columns["fat_per_100g"])),
                        "fiber_per_100g": decimal_or_none(row.get(columns["fiber_per_100g"])),
                    },
                )
                canonical_name = canonical_recipe_name(name, "bls", external_id)
                shopping_category, is_common_pantry = infer_product_taxonomy(
                    name,
                    canonical_name,
                    source="bls",
                    external_id=external_id,
                )
                products.append(Product(
                    source="bls", external_id=external_id, name=name[:150],
                    default_unit=suggested_unit_for_product(
                        name,
                        canonical_name,
                        shopping_category,
                    ),
                    canonical_name=canonical_name,
                    is_recipe_ingredient=is_recipe_ingredient,
                    recipe_exclusion_reason=exclusion_reason,
                    shopping_category=shopping_category,
                    is_common_pantry=is_common_pantry,
                    **nutrients,
                ))
            if options["dry_run"]:
                self.stdout.write(self.style.WARNING(f"Testlauf: {len(products)} BLS-Produkte erkannt; nichts gespeichert."))
                return
            Product.objects.bulk_create(
                products,
                batch_size=options["batch_size"],
                update_conflicts=True,
                unique_fields=["source", "external_id"],
                update_fields=[
                    "name", "canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason",
                    "shopping_category", "is_common_pantry",
                    "default_unit", "calories_per_100g", "protein_per_100g",
                    "carbohydrates_per_100g", "fat_per_100g", "fiber_per_100g",
                ],
            )
            ensure_curated_ingredients()
            rebuild_product_aliases(Product.objects.filter(source__in=("bls", "usda")))
            self.stdout.write(self.style.SUCCESS(f"{len(products)} BLS-Produkte importiert/aktualisiert."))
        finally:
            rows.close()
