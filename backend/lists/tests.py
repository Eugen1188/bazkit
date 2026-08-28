from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from products.models import Product
from recipes.models import Ingredients, Recipe

from .categories import shopping_category
from .models import ShoppingListItem
from .views import AddRecipeToShoppingListAPIView


class ShoppingCategoryTests(SimpleTestCase):
    def category_for(self, name, category=""):
        product = SimpleNamespace(
            name=name,
            canonical_name=name,
            category=category,
            shopping_category="other",
        )
        item = SimpleNamespace(name=name, product=product)
        return shopping_category(item)[0]

    def test_common_groceries_are_assigned_to_store_sections(self):
        self.assertEqual(self.category_for("Banane"), "produce")
        self.assertEqual(self.category_for("Vollmilch"), "dairy_eggs")
        self.assertEqual(self.category_for("Rind Hackfleisch"), "meat_fish")
        self.assertEqual(self.category_for("Spaghetti"), "pantry")
        self.assertEqual(self.category_for("Spülmittel"), "household")

    def test_saved_product_category_has_priority_over_name_fallback(self):
        product = SimpleNamespace(
            name="Ungewöhnlicher Name",
            canonical_name="Ungewöhnlicher Name",
            category="",
            shopping_category="produce",
        )
        item = SimpleNamespace(name=product.name, product=product)
        self.assertEqual(shopping_category(item)[0], "produce")


class AddRecipePantryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-test",
            email="pantry@example.com",
            password="test-password",
        )
        self.recipe = Recipe.objects.create(
            user=self.user,
            name="Kartoffeln mit Salz",
            servings=2,
            instructions="Kochen",
        )
        self.potato = Product.objects.create(
            name="Kartoffel",
            canonical_name="Kartoffel",
            shopping_category="produce",
            is_common_pantry=False,
        )
        self.salt = Product.objects.create(
            name="Salz",
            canonical_name="Salz",
            shopping_category="pantry",
            is_common_pantry=True,
        )
        Ingredients.objects.create(
            recipe=self.recipe,
            product=self.potato,
            name="Kartoffel",
            quantity="500",
            unit="g",
        )
        Ingredients.objects.create(
            recipe=self.recipe,
            product=self.salt,
            name="Salz",
            quantity="1",
            unit="Prise",
        )

    def test_recipe_import_skips_unselected_common_pantry_products(self):
        request = APIRequestFactory().post(
            f"/lists/shopping-list/add-recipe/{self.recipe.id}/",
            {"included_pantry_product_ids": []},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AddRecipeToShoppingListAPIView.as_view()(
            request,
            recipe_id=self.recipe.id,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(ShoppingListItem.objects.values_list("name", flat=True)),
            ["Kartoffel"],
        )
