import re

from django.db import migrations, models


AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b.*$",
    re.I,
)
PREPARED = re.compile(
    r"(?:suppe|eintopf|pfanne|auflauf|pizza|lasagne|burger|sandwich|wrap|"
    r"bami\s+goreng|nasi\s+goreng|gulasch|ragout|frikassee|risotto|paella|"
    r"fischstäbchen|fertiggericht|tellergericht|mahlzeit|gebraten|frittiert|"
    r"paniert|verzehrfertig|zubereitet|gekocht|gegart|überbacken)\b",
    re.I,
)
NON_INGREDIENT = re.compile(
    r"\b(?:limonade|cola|energydrink|erfrischungsgetränk|eistee|torte|kuchen|"
    r"muffin|keks|plätzchen|praline|chips|cracker|bonbon|dessert|pudding)\b",
    re.I,
)
OFF_MEAL_CATEGORY = re.compile(r"(?:^|[,; ])(?:meals?|pizzas?|prepared-meals?)(?:$|[,; ])", re.I)


def canonical_name(value):
    name = AMOUNT_SUFFIX.sub("", re.sub(r"\s+", " ", str(value or "")).strip()).strip(" ,-–")
    for pattern, replacement in (
        (r"^(?:h-)?milch\b|^vollmilch\b", "Milch"),
        (r"^buttermilch\b", "Buttermilch"),
        (r"^kokos(?:nuss)?milch\b", "Kokosmilch"),
        (r"^(?:hähnchen|huhn|hühner)brust", "Hähnchenbrust"),
        (r"^tomaten?\b", "Tomate"),
        (r"^zwiebeln?\b", "Zwiebel"),
        (r"^knoblauch\b", "Knoblauch"),
        (r"^kartoffeln?\b", "Kartoffel"),
        (r"^(?:karotten?|möhren?)\b", "Karotte"),
        (r"^(?:salat)?gurken?\b", "Gurke"),
        (r"^äpfel?\b|^apfel\b", "Apfel"),
        (r"^bananen?\b", "Banane"),
    ):
        if re.search(pattern, name, re.I):
            return replacement
    result = re.sub(r"\([^)]*\)", "", name).split(",", 1)[0]
    result = re.sub(r"\b(?:roh|frisch|tiefgefroren|pasteurisiert)\b", "", result, flags=re.I)
    return (re.sub(r"\s+", " ", result).strip(" ,-–/") or name)[:150]


def populate_recipe_catalog(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    pending = []
    for product in Product.objects.all().iterator(chunk_size=500):
        searchable = f"{product.name} {product.category or ''}"
        is_ingredient = not PREPARED.search(searchable) and not NON_INGREDIENT.search(searchable)
        reason = ""
        if product.source == "bls" and str(product.external_id or "").upper().startswith("Y"):
            is_ingredient = False
            reason = "BLS-Rezeptur oder zusammengesetzte Speise"
        elif product.source == "open_food_facts" and OFF_MEAL_CATEGORY.search(product.category or ""):
            is_ingredient = False
            reason = "Open-Food-Facts-Kategorie Fertiggericht"
        elif not is_ingredient:
            reason = "Fertiggericht oder kein typisches Kochprodukt"
        product.canonical_name = canonical_name(product.name)
        product.is_recipe_ingredient = is_ingredient
        product.recipe_exclusion_reason = reason
        pending.append(product)
        if len(pending) == 500:
            Product.objects.bulk_update(
                pending,
                ["canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason"],
            )
            pending.clear()
    if pending:
        Product.objects.bulk_update(
            pending,
            ["canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason"],
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_product_brand_product_created_at_product_external_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="canonical_name",
            field=models.CharField(blank=True, db_index=True, max_length=150),
        ),
        migrations.AddField(
            model_name="product",
            name="is_recipe_ingredient",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name="product",
            name="recipe_exclusion_reason",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.CreateModel(
            name="IngredientPriceReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_name", models.CharField(db_index=True, max_length=150)),
                ("category_tag", models.CharField(max_length=150)),
                ("basis", models.CharField(choices=[("kg", "Kilogramm"), ("unit", "Stück")], max_length=10)),
                ("median_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("price_min", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("price_max", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("currency", models.CharField(default="EUR", max_length=3)),
                ("region", models.CharField(default="DE", max_length=10)),
                ("observation_count", models.PositiveIntegerField(default=0)),
                ("location_count", models.PositiveIntegerField(default=0)),
                ("newest_price_date", models.DateField(blank=True, null=True)),
                ("confidence", models.CharField(choices=[("low", "Niedrig"), ("medium", "Mittel"), ("high", "Hoch")], default="low", max_length=10)),
                ("source", models.CharField(default="open_prices_category", max_length=40)),
                ("is_active", models.BooleanField(db_index=True, default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [models.Index(fields=["canonical_name", "is_active"], name="prod_price_name_active_idx")],
                "constraints": [models.UniqueConstraint(fields=("canonical_name", "category_tag", "basis", "region"), name="unique_ingredient_price_reference")],
            },
        ),
        migrations.RunPython(populate_recipe_catalog, migrations.RunPython.noop),
    ]
