from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .catalog import canonical_recipe_name, canonical_search_query, recipe_ingredient_status
from .ingredient_catalog import canonical_query, replace_product_aliases
from .models import IngredientPriceReference, Product
from .pricing import estimate_product_price
from .views import ProductSearchAPIView, nutrition_is_complete, usda_payload


COMPLETE_NUTRITION = {
    "calories_per_100g": Decimal("20.00"),
    "protein_per_100g": Decimal("1.00"),
    "carbohydrates_per_100g": Decimal("3.00"),
    "fat_per_100g": Decimal("0.20"),
    "fiber_per_100g": Decimal("1.00"),
}


class RecipeCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-test",
            email="catalog@example.com",
            password="test-password",
        )

    def test_catalog_classification_and_canonical_name(self):
        self.assertEqual(canonical_recipe_name("H-Milch fettarm, 1,5 % Fett"), "Milch")
        self.assertEqual(canonical_recipe_name("Chilischoten, frisch"), "Chilischote")
        self.assertEqual(canonical_search_query("Chilischotten"), "Chilischote")
        self.assertEqual(canonical_search_query("Peperoni"), "Chilischote")
        self.assertEqual(recipe_ingredient_status("Kürbissuppe mit Kokosmilch")[0], False)
        self.assertEqual(recipe_ingredient_status("Chili sin carne")[0], False)
        self.assertEqual(recipe_ingredient_status("Chili con carne einfach")[0], False)
        self.assertEqual(recipe_ingredient_status("Hähnchenbrust, roh")[0], True)

    def test_recipe_search_shows_chili_pepper_and_hides_stale_chili_meals(self):
        curated_chili = Product.objects.get(
            source="usda",
            external_id="170497",
        )
        self.assertTrue(curated_chili.is_recipe_ingredient)
        self.assertEqual(curated_chili.calories_per_100g, Decimal("40.00"))
        Product.objects.create(
            name="Chili sin carne",
            canonical_name="Chili sin carne",
            source="bls",
            external_id="X4A8000",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Chili", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Chilischote")
        self.assertNotIn("Chili sin carne", [item["name"] for item in response.data])

        typo_request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Chilischotten", "recipe_only": "1"},
        )
        force_authenticate(typo_request, user=self.user)
        typo_response = ProductSearchAPIView.as_view()(typo_request)
        self.assertEqual(typo_response.data[0]["name"], "Chilischote")

    def test_recipe_search_prioritizes_canonical_milk_and_hides_meals(self):
        Product.objects.create(
            name="H-Milch fettarm, 1,5 % Fett",
            canonical_name="Milch",
            source="bls",
            external_id="M113200",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        Product.objects.create(
            name="Buttermilch",
            canonical_name="Buttermilch",
            source="bls",
            external_id="M150000",
            is_recipe_ingredient=True,
        )
        Product.objects.create(
            name="Kürbissuppe mit Kokosmilch",
            canonical_name="Kürbissuppe mit Kokosmilch",
            source="bls",
            external_id="X490263",
            is_recipe_ingredient=False,
        )
        request = APIRequestFactory().get("/products/search/", {"q": "Milch", "recipe_only": "1"})
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Milch")
        self.assertNotIn("Kürbissuppe mit Kokosmilch", [item["name"] for item in response.data])

    def test_dosentomaten_alias_finds_one_complete_generic_ingredient(self):
        first = Product.objects.create(
            name="Tomaten, Konserve",
            canonical_name=canonical_recipe_name("Tomaten, Konserve"),
            source="bls",
            external_id="G520200",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        duplicate = Product.objects.create(
            name="Tomaten gehackt",
            canonical_name=canonical_recipe_name("Tomaten gehackt"),
            source="open_food_facts",
            external_id="123456789",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(first)
        replace_product_aliases(duplicate)

        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Dosentomaten", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(canonical_query("Dosentomaten"), "Dosentomaten")
        self.assertEqual([item["name"] for item in response.data], ["Dosentomaten"])
        self.assertTrue(response.data[0]["nutrition_complete"])

    def test_incomplete_products_are_never_returned_for_recipes(self):
        product = Product.objects.create(
            name="Mangold roh",
            canonical_name="Mangold",
            source="bls",
            external_id="G480100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("19.00"),
        )
        replace_product_aliases(product)
        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Mangold", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_usda_payload_requires_and_maps_all_nutrients(self):
        product = usda_payload({
            "fdcId": 170457,
            "description": "Tomatoes, red, ripe, canned",
            "dataType": "SR Legacy",
            "foodNutrients": [
                {"nutrientId": 1008, "nutrientName": "Energy", "unitName": "KCAL", "value": 18},
                {"nutrientId": 1003, "nutrientName": "Protein", "unitName": "G", "value": 0.95},
                {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "unitName": "G", "value": 4.01},
                {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "unitName": "G", "value": 0.11},
                {"nutrientId": 1079, "nutrientName": "Fiber, total dietary", "unitName": "G", "value": 1.2},
            ],
        }, "Dosentomaten")
        self.assertEqual(product["name"], "Dosentomaten")
        self.assertTrue(nutrition_is_complete(product))
        self.assertEqual(product["source"], "usda")

    def test_reference_price_is_scaled_automatically(self):
        product = Product.objects.create(
            name="Tomate roh",
            canonical_name="Tomate",
            source="bls",
            external_id="G520100",
            is_recipe_ingredient=True,
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
        estimate = estimate_product_price(product, Decimal("250"), "g")
        self.assertTrue(estimate["available"])
        self.assertEqual(estimate["estimated_price"], Decimal("0.75"))
        self.assertEqual(estimate["price_source"], "open_prices_category")

    def test_low_confidence_reference_uses_average_piece_weight(self):
        product = Product.objects.create(
            name="Banane roh",
            canonical_name="Banane",
            source="bls",
            external_id="F110100",
            is_recipe_ingredient=True,
        )
        IngredientPriceReference.objects.create(
            canonical_name="Banane",
            category_tag="en:bananas",
            basis="kg",
            median_price=Decimal("2.00"),
            price_min=Decimal("1.50"),
            price_max=Decimal("2.50"),
            observation_count=1,
            location_count=1,
            confidence="low",
            is_active=True,
        )
        estimate = estimate_product_price(product, Decimal("1"), "Stück")
        self.assertTrue(estimate["available"])
        self.assertEqual(estimate["estimated_price"], Decimal("0.24"))
        self.assertEqual(estimate["confidence"], "low")
