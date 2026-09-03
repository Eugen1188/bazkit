import re
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework import serializers

from products.catalog import ingredient_quantity_grams, recipe_ingredient_status
from products.models import Product
from products.pricing import estimate_product_price
from products.serializers import ProductSerializer
from .models import Ingredients, Recipe
from .storage import get_recipe_image_url


AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)
MINIMUM_PRICE_COVERAGE = Decimal("0.70")


def clean_product_name(value):
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    return AMOUNT_SUFFIX.sub("", name).strip(" ,-–")[:100]


def calculate_recipe_nutrition(recipe, ingredients):
    totals = {field: Decimal("0") for field in ("calories", "protein", "carbohydrates", "fat", "fiber")}
    found = {field: False for field in totals}
    for ingredient in ingredients:
        if ingredient.quantity is None or ingredient.product is None:
            continue
        grams = ingredient_quantity_grams(
            ingredient.product.canonical_name or ingredient.product.name,
            ingredient.quantity,
            ingredient.unit,
            product=ingredient.product,
        )
        if grams is None:
            continue
        portions_of_100g = grams / Decimal("100")
        for target, source in (
            ("calories", "calories_per_100g"), ("protein", "protein_per_100g"),
            ("carbohydrates", "carbohydrates_per_100g"), ("fat", "fat_per_100g"),
            ("fiber", "fiber_per_100g"),
        ):
            value = getattr(ingredient.product, source)
            if value is not None:
                totals[target] += value * portions_of_100g
                found[target] = True
    servings = Decimal(recipe.servings or 1)
    for field in totals:
        setattr(recipe, field, (totals[field] / servings).quantize(Decimal("0.01")) if found[field] else None)
    recipe.save(update_fields=list(totals))


def recipe_price_coverage(ingredients):
    ingredients = list(ingredients)
    ingredient_count = len(ingredients)
    priced_ingredient_count = sum(
        ingredient.estimated_price is not None for ingredient in ingredients
    )
    ratio = (
        Decimal(priced_ingredient_count) / Decimal(ingredient_count)
        if ingredient_count else Decimal("0")
    )
    coverage_percent = int(
        (ratio * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    return {
        "ingredient_count": ingredient_count,
        "priced_ingredient_count": priced_ingredient_count,
        "missing_ingredient_count": ingredient_count - priced_ingredient_count,
        "coverage_percent": coverage_percent,
        "is_complete": ingredient_count > 0 and priced_ingredient_count == ingredient_count,
        "is_sufficient": ingredient_count > 0 and ratio >= MINIMUM_PRICE_COVERAGE,
    }


def calculate_recipe_price(recipe, ingredients):
    ingredients = list(ingredients)
    coverage = recipe_price_coverage(ingredients)
    prices = [
        ingredient.estimated_price
        for ingredient in ingredients
        if ingredient.estimated_price is not None
    ]
    recipe.estimated_price = (
        sum(prices).quantize(Decimal("0.01"))
        if prices and coverage["is_sufficient"] else None
    )
    recipe.save(update_fields=["estimated_price"])


def apply_automatic_price(attrs):
    estimate = estimate_product_price(
        attrs["product"],
        attrs.get("quantity"),
        attrs.get("unit"),
        mode="consumption",
    )
    if not estimate.get("available"):
        attrs.update({
            "estimated_price": None,
            "price_source": "",
            "price_currency": "EUR",
            "price_date": None,
            "price_store": "",
            "price_sample_count": 0,
            "price_min": None,
            "price_max": None,
            "package_price": None,
            "package_quantity": None,
            "package_unit": "",
        })
        return
    for field in (
        "estimated_price", "price_source", "price_currency", "price_date",
        "price_store", "price_sample_count", "price_min", "price_max",
        "package_price", "package_quantity", "package_unit",
    ):
        attrs[field] = estimate.get(field)


class IngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False, allow_blank=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), allow_null=True, required=False
    )
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = Ingredients
        fields = [
            "id", "product", "product_detail", "name", "quantity", "unit", "estimated_price",
            "price_source", "price_currency", "price_date", "price_store",
            "price_sample_count", "price_min", "price_max", "package_price",
            "package_quantity", "package_unit",
        ]
        read_only_fields = [
            "estimated_price", "price_source", "price_currency",
            "price_date", "price_store", "price_sample_count", "price_min",
            "price_max", "package_price", "package_quantity", "package_unit",
        ]

    def validate(self, attrs):
        product = attrs.get("product")
        if product is None:
            name = clean_product_name(attrs.get("name"))
            if not name:
                raise serializers.ValidationError({"name": "Bitte eine Zutat angeben."})
            attrs["name"] = name
            return attrs
        is_recipe_ingredient, exclusion_reason = recipe_ingredient_status(
            product.name,
            product.category,
            product.source,
            product.external_id,
        )
        if not product.is_recipe_ingredient or not is_recipe_ingredient:
            raise serializers.ValidationError({
                "product": exclusion_reason or (
                    "Dieses Produkt ist keine freigegebene Kochzutat. "
                    "Bitte wähle eine Zutat aus den Vorschlägen."
                )
            })
        if not product.has_complete_nutrition:
            raise serializers.ValidationError({
                "product": (
                    "Für diese Zutat sind die Nährwerte noch nicht vollständig. "
                    "Bitte wähle einen anderen, vollständig geprüften Treffer."
                )
            })
        attrs["name"] = clean_product_name(product.canonical_name or product.name)
        apply_automatic_price(attrs)
        return attrs


class RecipeSummarySerializer(serializers.ModelSerializer):
    """Small read-only representation for recipe cards and planner pickers."""

    image_url = serializers.SerializerMethodField()
    ingredient_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "description", "servings", "preparation_time", "category",
            "image_url", "image_position_x", "image_position_y", "image_zoom",
            "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "ingredient_count", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        return get_recipe_image_url(obj.image_key)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True, required=True)
    image_url = serializers.SerializerMethodField()
    estimated_price_per_serving = serializers.SerializerMethodField()
    price_ingredient_count = serializers.SerializerMethodField()
    price_missing_ingredient_count = serializers.SerializerMethodField()
    price_coverage_percent = serializers.SerializerMethodField()
    price_is_complete = serializers.SerializerMethodField()
    price_is_sufficient = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "description", "servings", "preparation_time", "category",
            "instructions", "notes", "image_url", "image_position_x", "image_position_y", "image_zoom",
            "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "estimated_price_per_serving", "price_ingredient_count",
            "price_missing_ingredient_count", "price_coverage_percent", "price_is_complete",
            "price_is_sufficient", "created_at", "updated_at", "ingredients",
        ]
        read_only_fields = [
            "id", "image_url", "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "estimated_price_per_serving", "created_at", "updated_at",
            "price_ingredient_count", "price_missing_ingredient_count", "price_coverage_percent",
            "price_is_complete", "price_is_sufficient",
        ]

    def get_image_url(self, obj):
        return get_recipe_image_url(obj.image_key)

    def get_price_coverage(self, obj):
        if not hasattr(obj, "_price_coverage_cache"):
            obj._price_coverage_cache = recipe_price_coverage(obj.ingredients.all())
        return obj._price_coverage_cache

    def get_price_ingredient_count(self, obj):
        return self.get_price_coverage(obj)["priced_ingredient_count"]

    def get_price_missing_ingredient_count(self, obj):
        return self.get_price_coverage(obj)["missing_ingredient_count"]

    def get_price_coverage_percent(self, obj):
        return self.get_price_coverage(obj)["coverage_percent"]

    def get_price_is_complete(self, obj):
        return self.get_price_coverage(obj)["is_complete"]

    def get_price_is_sufficient(self, obj):
        return self.get_price_coverage(obj)["is_sufficient"]

    def get_estimated_price_per_serving(self, obj):
        if obj.estimated_price is None or not obj.servings:
            return None
        return round(obj.estimated_price / Decimal(obj.servings), 2)

    def validate(self, attrs):
        for field in ("calories", "protein", "carbohydrates", "fat", "fiber"):
            value = attrs.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: "Der Wert darf nicht negativ sein."})
        ingredients = attrs.get("ingredients")
        if ingredients is not None and not ingredients:
            raise serializers.ValidationError({"ingredients": "Mindestens eine Zutat ist erforderlich."})
        if ingredients is not None:
            preserved_legacy = {}
            if self.instance is not None:
                preserved_legacy = {
                    ingredient.id: clean_product_name(ingredient.name).casefold()
                    for ingredient in self.instance.ingredients.filter(product__isnull=True)
                }
            used_legacy_ids = set()
            ingredient_errors = []
            for ingredient in ingredients:
                if ingredient.get("product") is not None:
                    ingredient_errors.append({})
                    continue
                ingredient_id = ingredient.get("id")
                normalized_name = clean_product_name(ingredient.get("name")).casefold()
                is_unchanged_legacy = (
                    ingredient_id in preserved_legacy
                    and ingredient_id not in used_legacy_ids
                    and preserved_legacy[ingredient_id] == normalized_name
                )
                if is_unchanged_legacy:
                    used_legacy_ids.add(ingredient_id)
                    ingredient_errors.append({})
                    continue
                ingredient_errors.append({
                    "product": (
                        "Bitte wähle diese Zutat aus den Produktvorschlägen aus. "
                        "Nur so können die Nährwerte zuverlässig berechnet werden."
                    )
                })
            if any(ingredient_errors):
                raise serializers.ValidationError({"ingredients": ingredient_errors})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(user=self.context["request"].user, **validated_data)
        created_ingredients = []
        for item in ingredients:
            item.pop("id", None)
            created_ingredients.append(Ingredients.objects.create(recipe=recipe, **item))
        calculate_recipe_nutrition(recipe, created_ingredients)
        calculate_recipe_price(recipe, created_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if ingredients is not None:
            instance.ingredients.all().delete()
            created_ingredients = []
            for item in ingredients:
                item.pop("id", None)
                created_ingredients.append(Ingredients.objects.create(recipe=instance, **item))
            calculate_recipe_nutrition(instance, created_ingredients)
            calculate_recipe_price(instance, created_ingredients)
        else:
            existing_ingredients = list(instance.ingredients.select_related("product"))
            calculate_recipe_nutrition(instance, existing_ingredients)
            calculate_recipe_price(instance, existing_ingredients)
        return instance


class GenerateRecipeSerializer(serializers.Serializer):
    idea = serializers.CharField(required=False, allow_blank=True, max_length=500)
    available_ingredients = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    avoid_ingredients = serializers.CharField(required=False, allow_blank=True, max_length=500)
    diet = serializers.ChoiceField(
        choices=["none", "vegetarian", "vegan", "high_protein", "low_carb"],
        default="none",
    )
    servings = serializers.IntegerField(min_value=1, max_value=20, default=2)
    max_time = serializers.IntegerField(min_value=5, max_value=240, default=30)
    category = serializers.ChoiceField(
        choices=["breakfast", "lunch", "dinner", "snack", "dessert", "other"],
        default="dinner",
    )

    def validate(self, attrs):
        idea = attrs.get("idea", "").strip()
        available = attrs.get("available_ingredients", "").strip()
        if not idea and not available:
            raise serializers.ValidationError({
                "detail": "Gib entweder eine Rezeptidee oder vorhandene Zutaten an."
            })
        return attrs
