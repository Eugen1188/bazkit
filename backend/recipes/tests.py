import json
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from products.models import IngredientPriceReference, Product, ProductUnitConversion
from products.catalog import sync_curated_unit_conversion
from .models import Ingredients, Recipe
from .serializers import RecipeSerializer, calculate_recipe_price
from .storage import prepare_recipe_image
from .ai_service import generate_recipe_with_ai


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
            carbohydrates_per_100g=Decimal("3.5"),
            fat_per_100g=Decimal("0.2"),
            fiber_per_100g=Decimal("1.1"),
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

    def test_free_text_ingredient_is_kept_without_creating_product(self):
        serializer = RecipeSerializer(data={
            "name": "Familienrezept", "servings": 2, "category": "dinner",
            "instructions": "1. Vermengen", "ingredients": [{
                "product": None, "name": "Omas Gewürzmischung",
                "quantity": "1", "unit": "Prise",
            }],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        recipe = serializer.save()
        ingredient = recipe.ingredients.get()
        self.assertIsNone(ingredient.product)
        self.assertEqual(ingredient.name, "Omas Gewürzmischung")
        self.assertIsNone(recipe.calories)

    @override_settings(OPENAI_API_KEY="test-key", OPENAI_RECIPE_MODEL="test-model")
    @patch("recipes.ai_service.OpenAI")
    def test_ai_recipe_uses_verified_product_and_returns_nutrition(self, openai_mock):
        openai_mock.return_value.responses.create.return_value.output_text = json.dumps({
            "name": "Tomatensalat",
            "description": "Ein schneller Salat.",
            "servings": 2,
            "preparation_time": 10,
            "category": "lunch",
            "ingredients": [{
                "product_id": self.product.id,
                "quantity": 200,
                "unit": "g",
            }],
            "steps": ["Tomaten schneiden und servieren."],
            "notes": "Frisch genießen.",
        })

        result = generate_recipe_with_ai({
            "idea": "Tomatensalat",
            "available_ingredients": "Tomate",
            "avoid_ingredients": "",
            "diet": "vegan",
            "servings": 2,
            "max_time": 15,
            "category": "lunch",
        })

        self.assertTrue(result["nutrition_complete"])
        self.assertEqual(result["ingredients"][0]["product"], self.product.id)
        self.assertEqual(result["ingredients"][0]["name"], "Tomate")
        self.assertEqual(result["nutrition"]["calories"], 20.0)

    def test_image_position_is_saved_and_defaults_to_center(self):
        serializer = RecipeSerializer(data={
            "name": "Bildausschnitt", "servings": 2, "category": "dinner",
            "instructions": "1. Kochen", "image_position_x": 24,
            "image_position_y": 78, "ingredients": [{
                "product": self.product.id, "name": "Tomate",
                "quantity": "100", "unit": "g",
            }],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        recipe = serializer.save()
        self.assertEqual(recipe.image_position_x, 24)
        self.assertEqual(recipe.image_position_y, 78)

        centered = Recipe.objects.create(
            user=self.user, name="Mittig", servings=1,
            category="other", instructions="1. Fertig",
        )
        self.assertEqual(centered.image_position_x, 50)
        self.assertEqual(centered.image_position_y, 50)

    def test_image_position_rejects_values_outside_frame(self):
        serializer = RecipeSerializer(data={
            "name": "Ungültiger Ausschnitt", "servings": 2, "category": "dinner",
            "instructions": "1. Kochen", "image_position_x": 101,
            "image_position_y": -1, "ingredients": [{
                "product": self.product.id, "name": "Tomate",
                "quantity": "100", "unit": "g",
            }],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertFalse(serializer.is_valid())
        self.assertIn("image_position_x", serializer.errors)
        self.assertIn("image_position_y", serializer.errors)

    def test_canned_tomato_nutrition_uses_full_can_weight(self):
        tomatoes = Product.objects.create(
            name="Tomaten Konserve", canonical_name="Dosentomaten",
            source="bls", external_id="dose-test", is_recipe_ingredient=True,
            calories_per_100g=Decimal("19"), protein_per_100g=Decimal("1.15"),
            carbohydrates_per_100g=Decimal("2.54"), fat_per_100g=Decimal("0.2"),
            fiber_per_100g=Decimal("1.0"),
        )
        sync_curated_unit_conversion(tomatoes)
        serializer = RecipeSerializer(data={
            "name": "Dosentest", "servings": 1, "category": "dinner",
            "instructions": "1. Kochen", "ingredients": [{
                "product": tomatoes.id, "name": "Dosentomaten",
                "quantity": "1", "unit": "Dose",
            }],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        recipe = serializer.save()
        self.assertEqual(recipe.calories, Decimal("76.00"))

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

    def test_ingredient_without_complete_nutrition_is_rejected(self):
        incomplete = Product.objects.create(
            name="Mangold roh",
            canonical_name="Mangold",
            source="bls",
            external_id="G480100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("19"),
        )
        serializer = RecipeSerializer(data={
            "name": "Unvollständige Nährwerte",
            "description": "",
            "servings": 2,
            "category": "dinner",
            "instructions": "1. Kochen",
            "ingredients": [{"product": incomplete.id, "quantity": "100", "unit": "g"}],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Nährwerte", str(serializer.errors["ingredients"][0]["product"][0]))

    def test_stale_prepared_meal_flag_cannot_bypass_runtime_filter(self):
        prepared = Product.objects.create(
            name="Chili sin carne",
            canonical_name="Chili sin carne",
            source="bls",
            external_id="X4A8000",
            is_recipe_ingredient=True,
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
            protein_per_100g=Decimal("1.1"),
            carbohydrates_per_100g=Decimal("22.8"),
            fat_per_100g=Decimal("0.3"),
            fiber_per_100g=Decimal("2.6"),
        )
        ProductUnitConversion.objects.create(
            product=banana, unit="Stück", grams_per_unit=Decimal("120"),
            source="Geprüfte Portionsreferenz", confidence="reference",
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

    def test_recipe_image_is_optimized_as_webp(self):
        source = BytesIO()
        Image.new("RGB", (2400, 1200), color=(87, 126, 99)).save(source, format="JPEG")
        upload = SimpleUploadedFile(
            "gericht.jpg",
            source.getvalue(),
            content_type="image/jpeg",
        )

        optimized = prepare_recipe_image(upload)

        with Image.open(BytesIO(optimized)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertLessEqual(max(image.size), 1920)

    @patch("recipes.serializers.get_recipe_image_url", return_value="https://example.test/image.webp")
    @patch("recipes.views.upload_recipe_image", return_value="recipes/1/test.webp")
    def test_authenticated_owner_can_upload_recipe_image(self, upload_mock, _url_mock):
        recipe = Recipe.objects.create(
            user=self.user,
            name="Bildrezept",
            servings=2,
            category="dinner",
            instructions="1. Kochen",
        )
        client = APIClient()
        client.force_authenticate(self.user)
        upload = SimpleUploadedFile(
            "gericht.jpg",
            b"mock-image-content",
            content_type="image/jpeg",
        )

        response = client.post(f"/recipes/{recipe.id}/image/", {"image": upload}, format="multipart")

        self.assertEqual(response.status_code, 200)
        recipe.refresh_from_db()
        self.assertEqual(recipe.image_key, "recipes/1/test.webp")
        self.assertEqual(response.data["image_url"], "https://example.test/image.webp")
        upload_mock.assert_called_once()

    @patch("recipes.views.upload_recipe_image", return_value="recipes/2/forbidden.webp")
    def test_other_user_cannot_upload_recipe_image(self, upload_mock):
        other_user = get_user_model().objects.create_user(
            username="other-user",
            email="other@example.com",
            password="test-password",
        )
        recipe = Recipe.objects.create(
            user=other_user,
            name="Fremdes Rezept",
            servings=2,
            category="dinner",
            instructions="1. Kochen",
        )
        client = APIClient()
        client.force_authenticate(self.user)
        upload = SimpleUploadedFile("gericht.jpg", b"content", content_type="image/jpeg")

        response = client.post(f"/recipes/{recipe.id}/image/", {"image": upload}, format="multipart")

        self.assertEqual(response.status_code, 404)
        upload_mock.assert_not_called()
