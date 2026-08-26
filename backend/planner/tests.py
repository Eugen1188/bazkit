from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from lists.models import ShoppingListItem
from products.models import Product
from recipes.models import Ingredients, Recipe

from .models import WeeklyPlanEntry


@override_settings(OPENAI_API_KEY="")
class WeeklyPlannerAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="planner-test",
            email="planner@example.com",
            password="test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="planner-other",
            email="planner-other@example.com",
            password="test-password",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(
            name="Kartoffel",
            canonical_name="Kartoffel",
            source="bls",
            external_id="K100000",
            is_recipe_ingredient=True,
        )
        self.recipe = Recipe.objects.create(
            user=self.user,
            name="Kartoffelgericht",
            servings=2,
            category="dinner",
            instructions="Kochen",
            calories=Decimal("500"),
            protein=Decimal("20"),
        )
        Ingredients.objects.create(
            recipe=self.recipe,
            product=self.product,
            name="Kartoffel",
            quantity=Decimal("400"),
            unit="g",
            estimated_price=Decimal("0.80"),
            package_price=Decimal("2.00"),
            package_quantity=Decimal("1000"),
            package_unit="g",
            price_source="open_prices_category",
        )

    def test_slot_is_created_and_then_replaced(self):
        payload = {
            "date": "2026-08-24",
            "meal_type": "dinner",
            "servings": 2,
            "recipe": self.recipe.id,
        }
        first = self.client.post("/planner/entries/", payload, format="json")
        second = self.client.post(
            "/planner/entries/",
            {**payload, "servings": 4},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(WeeklyPlanEntry.objects.count(), 1)
        self.assertEqual(WeeklyPlanEntry.objects.get().servings, 4)

    def test_recipe_of_another_user_is_rejected(self):
        foreign_recipe = Recipe.objects.create(
            user=self.other_user,
            name="Fremdes Rezept",
            servings=1,
            category="lunch",
            instructions="Kochen",
        )
        response = self.client.post("/planner/entries/", {
            "date": "2026-08-24",
            "meal_type": "lunch",
            "servings": 1,
            "recipe": foreign_recipe.id,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(WeeklyPlanEntry.objects.exists())

    def test_automatic_planner_fills_all_empty_slots(self):
        response = self.client.post("/planner/generate/", {
            "start": "2026-08-24",
            "end": "2026-08-30",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["changed_count"], 21)
        self.assertEqual(WeeklyPlanEntry.objects.count(), 21)

    def test_weekly_shopping_list_aggregates_and_scales_ingredients(self):
        for day_value in (date(2026, 8, 24), date(2026, 8, 25)):
            WeeklyPlanEntry.objects.create(
                user=self.user,
                recipe=self.recipe,
                date=day_value,
                meal_type="dinner",
                servings=1,
            )
        response = self.client.post("/planner/shopping-list/", {
            "start": "2026-08-24",
            "end": "2026-08-30",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_count"], 1)
        item = ShoppingListItem.objects.get()
        self.assertEqual(item.quantity, Decimal("400.00"))
        self.assertEqual(item.estimated_price, Decimal("2.00"))
