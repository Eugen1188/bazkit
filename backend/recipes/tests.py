from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from products.models import IngredientPriceReference, Product
from .models import Ingredients, Recipe
from .serializers import RecipeSerializer, calculate_recipe_price


class RecipeSerializerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="recipe-test",
            email="recipe@example.com",
            password="test-password",
        )
        self.product = Product.objects.create(
            name="Tomate roh",
            canonical_name="Tomate",
            source="bls",
            external_id="G520100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("20"),
            protein_per_100g=Decimal("1"),
        )
        IngredientPriceReference.objects.create(
            canonical_name="Tomate",
            category_tag="en:tomatoes",
            basis="kg",
            median_price=Decimal("3.00"),
            price_min=Decimal("2.50"),
            price_max=Decimal("3.50"),
            observation_count=12,
            location_count=4,
            confidence="high",
            is_active=True,
        )

    def test_recipe_ignores_manual_prices_and_calculates_price_and_nutrition(self):
        serializer = RecipeSerializer(data={
            "name": "Tomatenrezept",
            "description": "",
            "servings": 2,
            "preparation_time": 15,
            "category": "dinner",
            "instructions": "1. Schneiden",
            "notes": "",
            "estimated_price": "99.00",
            "ingredients": [{
                "product": self.product.id,
                "name": "Fantasiename",
                "quantity": "200",
                "unit": "g",
                "estimated_price": "88.00",
                "price_source": "manual",
            }],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        recipe = serializer.save()
        ingredient = recipe.ingredients.get()
        self.assertEqual(ingredient.name, "Tomate")
        self.assertEqual(ingredient.estimated_price, Decimal("0.60"))
        self.assertEqual(ingredient.price_source, "open_prices_category")
        self.assertEqual(recipe.estimated_price, Decimal("0.60"))
        self.assertEqual(recipe.calories, Decimal("20.00"))

    def test_non_ingredient_product_is_rejected(self):
        prepared = Product.objects.create(
            name="Kürbissuppe",
            canonical_name="Kürbissuppe",
            source="bls",
            external_id="X490263",
            is_recipe_ingredient=False,
        )
        serializer = RecipeSerializer(data={
            "name": "Nicht erlaubt",
            "description": "",
            "servings": 2,
            "category": "dinner",
            "instructions": "1. Öffnen",
            "ingredients": [{"product": prepared.id, "quantity": "1", "unit": "Stück"}],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertFalse(serializer.is_valid())
        self.assertIn("product", serializer.errors["ingredients"][0])

    def test_piece_ingredient_uses_average_weight_for_nutrition(self):
        banana = Product.objects.create(
            name="Banane roh",
            canonical_name="Banane",
            source="bls",
            external_id="F110100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("89"),
        )
        IngredientPriceReference.objects.create(
            canonical_name="Banane",
            category_tag="en:bananas",
            basis="kg",
            median_price=Decimal("2.00"),
            observation_count=1,
            location_count=1,
            confidence="low",
            is_active=True,
        )
        serializer = RecipeSerializer(data={
            "name": "Bananenrezept",
            "description": "",
            "servings": 1,
            "preparation_time": 5,
            "category": "snack",
            "instructions": "1. Schälen",
            "ingredients": [{"product": banana.id, "quantity": "1", "unit": "Stück"}],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        recipe = serializer.save()
        self.assertEqual(recipe.calories, Decimal("106.80"))
        self.assertEqual(recipe.estimated_price, Decimal("0.24"))

    def test_price_is_hidden_below_seventy_percent_coverage(self):
        recipe = Recipe.objects.create(
            user=self.user,
            name="Unvollständige Preise",
            servings=2,
            category="dinner",
            instructions="1. Kochen",
        )
        ingredients = [
            Ingredients.objects.create(
                recipe=recipe, product=self.product, name=f"Zutat {index}",
                quantity=Decimal("100"), unit="g",
                estimated_price=price, price_source="open_prices_category" if price else "",
            )
            for index, price in enumerate((Decimal("1.00"), Decimal("2.00"), None), start=1)
        ]
        calculate_recipe_price(recipe, ingredients)
        recipe.refresh_from_db()
        data = RecipeSerializer(recipe).data
        self.assertIsNone(recipe.estimated_price)
        self.assertEqual(data["price_ingredient_count"], 2)
        self.assertEqual(data["price_missing_ingredient_count"], 1)
        self.assertEqual(data["price_coverage_percent"], 67)
        self.assertFalse(data["price_is_sufficient"])

    def test_partial_price_is_shown_at_seventy_percent_coverage(self):
        recipe = Recipe.objects.create(
            user=self.user,
            name="Ausreichende Preise",
            servings=2,
            category="dinner",
            instructions="1. Kochen",
        )
        ingredients = [
            Ingredients.objects.create(
                recipe=recipe, product=self.product, name=f"Zutat {index}",
                quantity=Decimal("100"), unit="g",
                estimated_price=price, price_source="open_prices_category" if price else "",
            )
            for index, price in enumerate(
                (Decimal("1.00"), Decimal("2.00"), Decimal("3.00"), None), start=1
            )
        ]
        calculate_recipe_price(recipe, ingredients)
        recipe.refresh_from_db()
        data = RecipeSerializer(recipe).data
        self.assertEqual(recipe.estimated_price, Decimal("6.00"))
        self.assertEqual(data["price_coverage_percent"], 75)
        self.assertFalse(data["price_is_complete"])
        self.assertTrue(data["price_is_sufficient"])
