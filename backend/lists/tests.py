from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from products.models import Product
from recipes.models import Ingredients, Recipe

from .categories import shopping_category
from .models import (
    SavedList,
    SavedListInvitation,
    SavedListItem,
    SavedListMembership,
    ShoppingListItem,
)
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


class SavedListSummaryTests(TestCase):
    def test_overview_omits_items_but_keeps_item_count(self):
        user = get_user_model().objects.create_user(
            username="saved-list-test",
            email="saved-list@example.com",
            password="test-password",
        )
        saved_list = SavedList.objects.create(user=user, title="Wochenende")
        SavedListItem.objects.create(
            saved_list=saved_list,
            name="Milch",
            quantity=1,
            unit="Liter",
        )
        client = APIClient()
        client.force_authenticate(user)

        response = client.get("/lists/saved-lists/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["item_count"], 1)
        self.assertNotIn("items", response.data[0])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://frontend.test",
)
class SavedListCollaborationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner@example.com", email="owner@example.com",
            first_name="Olivia", password="test-password",
        )
        self.editor = user_model.objects.create_user(
            username="editor@example.com", email="editor@example.com",
            first_name="Emil", password="test-password",
        )
        self.viewer = user_model.objects.create_user(
            username="viewer@example.com", email="viewer@example.com",
            first_name="Vera", password="test-password",
        )
        self.saved_list = SavedList.objects.create(
            user=self.owner, title="Gemeinsamer Einkauf",
        )
        self.item = SavedListItem.objects.create(
            saved_list=self.saved_list, created_by=self.owner,
            name="Milch", quantity=1, unit="Liter",
        )

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_shared_list_appears_in_member_overview(self):
        SavedListMembership.objects.create(
            saved_list=self.saved_list, user=self.editor, role="editor",
        )
        response = self.client_for(self.editor).get("/lists/saved-lists/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], self.saved_list.id)
        self.assertEqual(response.data[0]["access_role"], "editor")
        self.assertFalse(response.data[0]["is_owner"])

    def test_viewer_can_read_but_cannot_change_or_check_items(self):
        SavedListMembership.objects.create(
            saved_list=self.saved_list, user=self.viewer, role="viewer",
        )
        client = self.client_for(self.viewer)
        detail = client.get(f"/lists/saved-lists/{self.saved_list.id}/")
        update = client.put(
            f"/lists/saved-lists/{self.saved_list.id}/",
            {"title": "Geändert", "items": []}, format="json",
        )
        toggle = client.patch(
            f"/lists/saved-lists/{self.saved_list.id}/items/{self.item.id}/toggle/",
            {"is_checked": True}, format="json",
        )
        self.assertEqual(detail.status_code, 200)
        self.assertFalse(detail.data["can_edit"])
        self.assertEqual(update.status_code, 403)
        self.assertEqual(toggle.status_code, 403)

    def test_email_invitation_can_be_accepted_and_editor_can_check_item(self):
        created = self.client_for(self.owner).post(
            f"/lists/saved-lists/{self.saved_list.id}/collaboration/",
            {"email": self.editor.email, "role": "editor"}, format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data["email_sent"])
        invitation = SavedListInvitation.objects.get(pk=created.data["id"])
        editor_client = self.client_for(self.editor)
        accepted = editor_client.post(
            f"/lists/saved-list-invitations/{invitation.token}/", {}, format="json",
        )
        toggled = editor_client.patch(
            f"/lists/saved-lists/{self.saved_list.id}/items/{self.item.id}/toggle/",
            {"is_checked": True}, format="json",
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(toggled.status_code, 200)
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_checked)
        self.assertEqual(self.item.checked_by, self.editor)

    def test_email_invitation_rejects_a_different_account(self):
        invitation = SavedListInvitation.objects.create(
            saved_list=self.saved_list, invited_by=self.owner,
            email=self.editor.email, role="editor",
        )
        response = self.client_for(self.viewer).post(
            f"/lists/saved-list-invitations/{invitation.token}/", {}, format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SavedListMembership.objects.filter(
            saved_list=self.saved_list, user=self.viewer,
        ).exists())
