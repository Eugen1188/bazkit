import re
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from products.catalog import ingredient_quantity_grams
from products.models import Product
from products.pricing import estimate_product_price
from products.serializers import ProductSerializer
from .models import Ingredients, Recipe


AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)
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


def calculate_recipe_price(recipe, ingredients):
    prices = [ingredient.estimated_price for ingredient in ingredients if ingredient.estimated_price is not None]
    recipe.estimated_price = sum(prices).quantize(Decimal("0.01")) if prices else None
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
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), allow_null=False, required=True)
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
            "id", "name", "estimated_price", "price_source", "price_currency",
            "price_date", "price_store", "price_sample_count", "price_min",
            "price_max", "package_price", "package_quantity", "package_unit",
        ]

    def validate(self, attrs):
        product = attrs.get("product")
        if product is None:
            raise serializers.ValidationError({"product": "Bitte ein Produkt aus den Vorschlägen auswählen."})
        if not product.is_recipe_ingredient:
            raise serializers.ValidationError({
                "product": "Dieses Produkt ist keine freigegebene Kochzutat. Bitte wähle eine Zutat aus den Vorschlägen."
            })
        attrs["name"] = clean_product_name(product.canonical_name or product.name)
        apply_automatic_price(attrs)
        return attrs


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True, required=True)
    estimated_price_per_serving = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "description", "servings", "preparation_time", "category",
            "instructions", "notes", "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "estimated_price_per_serving", "created_at", "updated_at", "ingredients",
        ]
        read_only_fields = [
            "id", "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "estimated_price_per_serving", "created_at", "updated_at",
        ]

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
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(user=self.context["request"].user, **validated_data)
        created_ingredients = [Ingredients.objects.create(recipe=recipe, **item) for item in ingredients]
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
            created_ingredients = [Ingredients.objects.create(recipe=instance, **item) for item in ingredients]
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
