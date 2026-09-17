from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient, APITestCase

from lists.models import SavedList, SavedListItem
from products.models import Product
from recipes.models import Ingredients, Recipe

from .models import (
    CommunityBlock,
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityRating,
    CommunityReport,
)


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
            image_position_x=22,
            image_position_y=74,
            image_zoom=138,
            calories=Decimal("420"),
            protein=Decimal("12"),
        )
        Ingredients.objects.create(
            recipe=self.recipe,
            product=self.product,
            name="Kartoffel",
            quantity=Decimal("500"),
            unit="g",
            note="geschält",
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
        self.assertEqual(post.recipe.ingredients.get().note, "geschält")
        self.assertEqual(post.recipe.calories, Decimal("420"))
        self.assertEqual(post.recipe.image_position_x, 22)
        self.assertEqual(post.recipe.image_position_y, 74)
        self.assertEqual(post.recipe.image_zoom, 138)
        self.assertEqual(response.data["recipe"]["image_position_x"], 22)
        self.assertEqual(response.data["recipe"]["image_position_y"], 74)
        self.assertEqual(response.data["recipe"]["image_zoom"], 138)
        self.assertEqual(response.data["recipe"]["ingredients"][0]["note"], "geschält")

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

    def test_post_list_uses_compact_payload_and_batched_metrics(self):
        created = self.client.post("/community/posts/", {
            "post_type": "recipe",
            "recipe_id": self.recipe.id,
        }, format="json")
        post = CommunityPost.objects.get(pk=created.data["id"])
        CommunityComment.objects.create(
            post=post,
            author=self.other_user,
            content="Sieht gut aus",
        )
        CommunityLike.objects.create(post=post, user=self.other_user)
        CommunityRating.objects.create(post=post, user=self.other_user, value=4)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/community/posts/")

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 4)
        listed_post = next(item for item in response.data if item["id"] == post.id)
        self.assertEqual(listed_post["comment_count"], 1)
        self.assertEqual(listed_post["like_count"], 0)
        self.assertEqual(listed_post["rating_count"], 1)
        self.assertEqual(listed_post["rating_average"], 4.0)
        self.assertNotIn("ingredients", listed_post["recipe"])

    def test_post_list_supports_bounded_pagination(self):
        for index in range(5):
            CommunityPost.objects.create(
                author=self.user,
                post_type="thread",
                title=f"Beitrag {index}",
                content="Inhalt",
                thread_category="other",
            )

        first_page = self.client.get("/community/posts/?limit=3&offset=0")
        second_page = self.client.get("/community/posts/?limit=3&offset=3")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(first_page.data), 3)
        self.assertEqual(len(second_page.data), 2)
        self.assertTrue(
            set(item["id"] for item in first_page.data).isdisjoint(
                item["id"] for item in second_page.data
            )
        )

    def test_recipe_rating_is_explicit_and_can_include_a_review(self):
        created = self.client.post("/community/posts/", {
            "post_type": "recipe",
            "recipe_id": self.recipe.id,
        }, format="json")
        post_id = created.data["id"]

        self.client.force_authenticate(self.other_user)
        rated = self.client.post(f"/community/posts/{post_id}/rating/", {
            "value": 5,
            "comment": "Einfach erklärt und sehr lecker.",
        }, format="json")

        self.assertEqual(rated.status_code, 200)
        self.assertEqual(rated.data["rating"], 5)
        self.assertEqual(rated.data["rating_comment"], "Einfach erklärt und sehr lecker.")
        self.assertEqual(rated.data["review"]["author"]["name"], "reader")

        detail = self.client.get(f"/community/posts/{post_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["my_rating"], 5)
        self.assertEqual(
            detail.data["my_rating_comment"],
            "Einfach erklärt und sehr lecker.",
        )
        self.assertEqual(len(detail.data["rating_reviews"]), 1)
        self.assertEqual(detail.data["rating_reviews"][0]["value"], 5)

    def test_recipes_cannot_be_liked_and_lists_cannot_be_rated(self):
        recipe_created = self.client.post("/community/posts/", {
            "post_type": "recipe",
            "recipe_id": self.recipe.id,
        }, format="json")
        recipe_like = self.client.post(
            f'/community/posts/{recipe_created.data["id"]}/like/',
            {},
            format="json",
        )
        self.assertEqual(recipe_like.status_code, 400)

        list_created = self.client.post("/community/posts/", {
            "post_type": "list",
            "saved_list_id": self.saved_list.id,
        }, format="json")
        list_rating = self.client.post(
            f'/community/posts/{list_created.data["id"]}/rating/',
            {"value": 4, "comment": "Unzulässig"},
            format="json",
        )
        self.assertEqual(list_rating.status_code, 400)

    def test_user_can_report_foreign_post_and_update_the_same_report(self):
        created = self.client.post("/community/posts/", {
            "post_type": "thread",
            "title": "Problematischer Beitrag",
            "content": "Inhalt",
            "thread_category": "other",
        }, format="json")
        post_id = created.data["id"]

        self.client.force_authenticate(self.other_user)
        reported = self.client.post(f"/community/posts/{post_id}/report/", {
            "reason": "spam",
            "details": "Wiederholte Werbung",
        }, format="json")
        self.assertEqual(reported.status_code, 201)
        self.assertEqual(CommunityReport.objects.count(), 1)

        updated = self.client.post(f"/community/posts/{post_id}/report/", {
            "reason": "other",
            "details": "Ergänzte Beschreibung",
        }, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(CommunityReport.objects.count(), 1)
        report = CommunityReport.objects.get()
        self.assertEqual(report.reason, "other")
        self.assertEqual(report.details, "Ergänzte Beschreibung")

    def test_user_cannot_report_own_post(self):
        created = self.client.post("/community/posts/", {
            "post_type": "thread",
            "title": "Eigener Beitrag",
            "content": "Inhalt",
            "thread_category": "other",
        }, format="json")
        response = self.client.post(
            f'/community/posts/{created.data["id"]}/report/',
            {"reason": "spam"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(CommunityReport.objects.exists())

    def test_blocked_users_are_hidden_in_both_directions_and_can_be_unblocked(self):
        post = CommunityPost.objects.create(
            author=self.other_user,
            post_type="thread",
            title="Unsichtbarer Beitrag",
            content="Dieser Inhalt wird blockiert.",
            thread_category="other",
        )

        blocked = self.client.post(
            f"/community/users/{self.other_user.id}/block/",
            {},
            format="json",
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertTrue(CommunityBlock.objects.filter(
            blocker=self.user,
            blocked=self.other_user,
        ).exists())
        self.assertEqual(self.client.get("/community/posts/").data, [])
        self.assertEqual(
            self.client.get(f"/community/posts/{post.id}/").status_code,
            404,
        )

        own_post = CommunityPost.objects.create(
            author=self.user,
            post_type="thread",
            title="Beitrag des Blockierenden",
            content="Auch dieser Beitrag wird in Gegenrichtung verborgen.",
            thread_category="other",
        )
        self.client.force_authenticate(self.other_user)
        other_posts = self.client.get("/community/posts/").data
        self.assertNotIn(own_post.id, [item["id"] for item in other_posts])

        self.client.force_authenticate(self.user)
        listed = self.client.get("/community/blocks/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data[0]["id"], self.other_user.id)
        unblocked = self.client.delete(
            f"/community/users/{self.other_user.id}/block/"
        )
        self.assertEqual(unblocked.status_code, 204)
        self.assertEqual(len(self.client.get("/community/posts/").data), 2)

    def test_duplicate_threads_and_comments_are_rejected(self):
        payload = {
            "post_type": "thread",
            "title": "Doppelt",
            "content": "Bitte nur einmal veröffentlichen.",
            "thread_category": "other",
        }
        first = self.client.post("/community/posts/", payload, format="json")
        second = self.client.post("/community/posts/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)

        post_id = first.data["id"]
        comment = {"content": "Gleicher Kommentar"}
        self.assertEqual(
            self.client.post(
                f"/community/posts/{post_id}/comments/", comment, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                f"/community/posts/{post_id}/comments/", comment, format="json"
            ).status_code,
            400,
        )
