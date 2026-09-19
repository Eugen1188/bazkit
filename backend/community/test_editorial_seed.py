from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase

from products.models import Product
from recipes.models import Recipe

from .editorial_content import EDITORIAL_PROFILES, EDITORIAL_RECIPES
from .models import CommunityPost


class EditorialCommunitySeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ingredient_names = sorted({
            ingredient[0]
            for recipe in EDITORIAL_RECIPES
            for ingredient in recipe["ingredients"]
        })
        Product.objects.bulk_create([
            Product(
                name=name,
                canonical_name=name,
                source="curated",
                external_id=f"editorial-test-{index}",
                is_recipe_ingredient=True,
                catalog_status="approved",
                default_unit="g",
                calories_per_100g=Decimal("100"),
                protein_per_100g=Decimal("5"),
                carbohydrates_per_100g=Decimal("10"),
                fat_per_100g=Decimal("4"),
                fiber_per_100g=Decimal("2"),
            )
            for index, name in enumerate(ingredient_names)
        ])

    def test_command_creates_and_updates_without_duplicates(self):
        first_output = StringIO()
        call_command("seed_editorial_community", stdout=first_output)

        User = get_user_model()
        usernames = [profile["username"] for profile in EDITORIAL_PROFILES]
        users = User.objects.filter(username__in=usernames)
        self.assertEqual(users.count(), len(EDITORIAL_PROFILES))
        self.assertTrue(all(not user.has_usable_password() for user in users))
        self.assertTrue(all(user.email_verified_at is not None for user in users))
        self.assertTrue(all(user.first_name.startswith("Bazkit ") for user in users))

        source_recipes = Recipe.objects.filter(
            user__username__in=usernames,
            is_community_snapshot=False,
        )
        snapshots = Recipe.objects.filter(
            user__username__in=usernames,
            is_community_snapshot=True,
        )
        posts = CommunityPost.objects.filter(
            author__username__in=usernames,
            post_type=CommunityPost.POST_TYPE_RECIPE,
        )
        self.assertEqual(source_recipes.count(), len(EDITORIAL_RECIPES))
        self.assertEqual(snapshots.count(), len(EDITORIAL_RECIPES))
        self.assertEqual(posts.count(), len(EDITORIAL_RECIPES))
        self.assertFalse(source_recipes.filter(ingredients__product__isnull=True).exists())

        post_ids = list(posts.order_by("id").values_list("id", flat=True))
        second_output = StringIO()
        call_command("seed_editorial_community", stdout=second_output)

        self.assertEqual(
            list(posts.order_by("id").values_list("id", flat=True)),
            post_ids,
        )
        self.assertEqual(source_recipes.count(), len(EDITORIAL_RECIPES))
        self.assertEqual(snapshots.count(), len(EDITORIAL_RECIPES))
        self.assertIn("0 Veröffentlichungen neu", second_output.getvalue())

    def test_command_never_adopts_a_real_user_account(self):
        profile = EDITORIAL_PROFILES[0]
        get_user_model().objects.create_user(
            username=profile["username"],
            email=profile["email"],
            password="real-user-password",
        )

        with self.assertRaises(CommandError):
            call_command("seed_editorial_community")

        self.assertEqual(CommunityPost.objects.count(), 0)
