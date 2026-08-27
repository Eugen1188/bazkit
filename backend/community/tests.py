from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from lists.models import SavedList, SavedListItem
from products.models import Product
from recipes.models import Ingredients, Recipe

from .models import CommunityPost


class CommunitySnapshotTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="publisher",
            email="publisher@example.com",
            password="test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
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
            name="Kartoffelsuppe",
            description="Original",
            servings=2,
            category="dinner",
            instructions="Kochen",
            calories=Decimal("420"),
            protein=Decimal("12"),
        )
        Ingredients.objects.create(
            recipe=self.recipe,
            product=self.product,
            name="Kartoffel",
            quantity=Decimal("500"),
            unit="g",
        )
        self.saved_list = SavedList.objects.create(user=self.user, title="Wocheneinkauf")
        SavedListItem.objects.create(
            saved_list=self.saved_list,
            product=self.product,
            name="Kartoffel",
            quantity=Decimal("1"),
            unit="kg",
        )

    def test_shared_recipe_is_an_independent_hidden_snapshot(self):
        response = self.client.post("/community/posts/", {
            "post_type": "recipe",
            "recipe_id": self.recipe.id,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        post = CommunityPost.objects.get(pk=response.data["id"])
        self.assertEqual(post.source_recipe_id, self.recipe.id)
        self.assertNotEqual(post.recipe_id, self.recipe.id)
        self.assertTrue(post.recipe.is_community_snapshot)
        self.assertEqual(post.recipe.ingredients.count(), 1)
        self.assertEqual(post.recipe.calories, Decimal("420"))

        self.recipe.name = "Geändertes Original"
        self.recipe.save(update_fields=["name"])
        self.assertEqual(response.data["display_title"], "Kartoffelsuppe")
        self.assertNotContains(self.client.get("/recipes/"), "Kartoffelsuppe")

        self.recipe.delete()
        post.refresh_from_db()
        self.assertIsNone(post.source_recipe_id)
        self.assertEqual(post.recipe.name, "Kartoffelsuppe")

    def test_deleting_recipe_post_keeps_original_and_removes_snapshot(self):
        response = self.client.post("/community/posts/", {
            "post_type": "recipe",
            "recipe_id": self.recipe.id,
        }, format="json")
        post = CommunityPost.objects.get(pk=response.data["id"])
        snapshot_id = post.recipe_id
        delete_response = self.client.delete(f"/community/posts/{post.id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.id).exists())
        self.assertFalse(Recipe.objects.filter(pk=snapshot_id).exists())

    def test_shared_list_is_independent(self):
        response = self.client.post("/community/posts/", {
            "post_type": "list",
            "saved_list_id": self.saved_list.id,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        post = CommunityPost.objects.get(pk=response.data["id"])
        self.assertNotEqual(post.saved_list_id, self.saved_list.id)
        self.assertTrue(post.saved_list.is_community_snapshot)
        self.assertEqual(post.saved_list.items.count(), 1)
        self.saved_list.delete()
        post.refresh_from_db()
        self.assertEqual(post.saved_list.title, "Wocheneinkauf")

    def test_author_can_edit_and_delete_thread_but_other_user_cannot(self):
        created = self.client.post("/community/posts/", {
            "post_type": "thread",
            "title": "Alter Titel",
            "content": "Alter Inhalt",
            "thread_category": "cooking",
        }, format="json")
        post_id = created.data["id"]
        updated = self.client.patch(f"/community/posts/{post_id}/", {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
        }, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["title"], "Neuer Titel")
        self.assertTrue(updated.data["is_author"])

        self.client.force_authenticate(self.other_user)
        forbidden = self.client.patch(f"/community/posts/{post_id}/", {
            "title": "Fremde Änderung",
        }, format="json")
        self.assertEqual(forbidden.status_code, 404)
