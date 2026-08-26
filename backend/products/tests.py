from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .catalog import canonical_recipe_name, recipe_ingredient_status
from .models import IngredientPriceReference, Product
from .pricing import estimate_product_price
from .views import ProductSearchAPIView


class RecipeCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-test",
            email="catalog@example.com",
            password="test-password",
        )

    def test_catalog_classification_and_canonical_name(self):
        self.assertEqual(canonical_recipe_name("H-Milch fettarm, 1,5 % Fett"), "Milch")
        self.assertEqual(recipe_ingredient_status("Kürbissuppe mit Kokosmilch")[0], False)
        self.assertEqual(recipe_ingredient_status("Hähnchenbrust, roh")[0], True)

    def test_recipe_search_prioritizes_canonical_milk_and_hides_meals(self):
        Product.objects.create(
            name="H-Milch fettarm, 1,5 % Fett",
            canonical_name="Milch",
            source="bls",
            external_id="M113200",
            is_recipe_ingredient=True,
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
