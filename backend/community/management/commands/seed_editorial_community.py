from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from community.editorial_content import EDITORIAL_PROFILES, EDITORIAL_RECIPES
from community.models import CommunityPost
from community.snapshots import INGREDIENT_FIELDS, RECIPE_FIELDS, clone_recipe
from products.models import Product
from recipes.models import Ingredients, Recipe
from recipes.serializers import calculate_recipe_nutrition


class Command(BaseCommand):
    help = (
        "Legt klar gekennzeichnete Bazkit-Redaktionsprofile mit kuratierten "
        "Community-Rezepten an. Der Befehl kann gefahrlos mehrfach laufen."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            profiles, created_profiles = self._ensure_profiles()
            created_recipes = 0
            updated_recipes = 0
            created_posts = 0
            updated_posts = 0
            unresolved_products = set()

            for definition in EDITORIAL_RECIPES:
                user = profiles[definition["profile"]]
                recipe, created, missing = self._upsert_recipe(user, definition)
                unresolved_products.update(missing)
                if created:
                    created_recipes += 1
                else:
                    updated_recipes += 1

                post_created = self._publish_or_refresh(user, recipe)
                if post_created:
                    created_posts += 1
                else:
                    updated_posts += 1

        if unresolved_products:
            self.stdout.write(self.style.WARNING(
                "Für folgende Zutaten wurde kein passender Katalogeintrag gefunden; "
                "sie bleiben als freie Zutaten ohne erfundene Nährwerte erhalten: "
                + ", ".join(sorted(unresolved_products))
            ))
        self.stdout.write(self.style.SUCCESS(
            f"Bazkit-Redaktion befüllt: {created_profiles} Profile neu, "
            f"{created_recipes} Rezepte neu, {updated_recipes} aktualisiert, "
            f"{created_posts} Veröffentlichungen neu, {updated_posts} aktualisiert."
        ))

    def _ensure_profiles(self):
        User = get_user_model()
        result = {}
        created_count = 0
        now = timezone.now()

        for definition in EDITORIAL_PROFILES:
            username = definition["username"]
            email = definition["email"]
            username_owner = User.objects.filter(username=username).first()
            email_owner = User.objects.filter(email=email).first()
            if username_owner and email_owner and username_owner.pk != email_owner.pk:
                raise CommandError(
                    f"Redaktionsprofil {username!r} und E-Mail {email!r} gehören "
                    "zu unterschiedlichen Konten. Es wurde nichts verändert."
                )
            if username_owner and username_owner.email != email:
                raise CommandError(
                    f"Der reservierte Profilname {username!r} wird bereits von einem "
                    "anderen Konto verwendet. Es wurde nichts verändert."
                )
            if email_owner and email_owner.username != username:
                raise CommandError(
                    f"Die reservierte Redaktionsadresse {email!r} wird bereits von einem "
                    "anderen Konto verwendet. Es wurde nichts verändert."
                )

            user = username_owner or email_owner
            if user is None:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    first_name=definition["display_name"],
                    email_verified_at=now,
                    terms_accepted_at=now,
                    terms_version=settings.LEGAL_TERMS_VERSION,
                    is_active=True,
                )
                created_count += 1
            else:
                if user.has_usable_password() or user.is_staff or user.is_superuser:
                    raise CommandError(
                        f"Das reservierte Redaktionsprofil {username!r} ist kein von "
                        "Bazkit verwaltetes Systemkonto. Es wurde nichts verändert."
                    )
                changed = []
                for field, value in (
                    ("first_name", definition["display_name"]),
                    ("email_verified_at", user.email_verified_at or now),
                    ("is_active", True),
                ):
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        changed.append(field)
                if changed:
                    user.save(update_fields=changed)
            result[username] = user

        return result, created_count

    def _resolve_product(self, canonical_name):
        complete = {
            "calories_per_100g__isnull": False,
            "protein_per_100g__isnull": False,
            "carbohydrates_per_100g__isnull": False,
            "fat_per_100g__isnull": False,
            "fiber_per_100g__isnull": False,
        }
        return (
            Product.objects.filter(
                canonical_name__iexact=canonical_name,
                catalog_status="approved",
                is_recipe_ingredient=True,
                **complete,
            )
            .annotate(source_priority=Case(
                When(source="curated", then=Value(0)),
                When(source="bls", then=Value(1)),
                When(source="usda", then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ))
            .order_by("source_priority", "id")
            .first()
        )

    def _upsert_recipe(self, user, definition):
        defaults = {
            field: definition[field]
            for field in (
                "description", "servings", "preparation_time", "category",
                "instructions", "notes",
            )
        }
        recipe, created = Recipe.objects.update_or_create(
            user=user,
            name=definition["name"],
            is_community_snapshot=False,
            defaults=defaults,
        )
        recipe.ingredients.all().delete()
        missing = []
        ingredients = []
        for name, quantity, unit, note in definition["ingredients"]:
            product = self._resolve_product(name)
            if product is None:
                missing.append(name)
            ingredients.append(Ingredients(
                recipe=recipe,
                product=product,
                name=name,
                quantity=Decimal(quantity),
                unit=unit,
                note=note,
            ))
        Ingredients.objects.bulk_create(ingredients)
        calculate_recipe_nutrition(recipe, ingredients)
        return recipe, created, missing

    def _publish_or_refresh(self, user, source_recipe):
        post = CommunityPost.objects.filter(
            author=user,
            post_type=CommunityPost.POST_TYPE_RECIPE,
            source_recipe=source_recipe,
        ).select_related("recipe").first()

        if post is None:
            snapshot = clone_recipe(source_recipe, user, community_snapshot=True)
            CommunityPost.objects.create(
                author=user,
                post_type=CommunityPost.POST_TYPE_RECIPE,
                source_recipe=source_recipe,
                recipe=snapshot,
            )
            return True

        snapshot = post.recipe
        if snapshot is None or not snapshot.is_community_snapshot:
            snapshot = clone_recipe(source_recipe, user, community_snapshot=True)
            post.recipe = snapshot
            post.save(update_fields=["recipe", "updated_at"])
            return False

        for field in RECIPE_FIELDS:
            setattr(snapshot, field, getattr(source_recipe, field))
        snapshot.is_community_snapshot = True
        snapshot.save(update_fields=[*RECIPE_FIELDS, "is_community_snapshot", "updated_at"])
        snapshot.ingredients.all().delete()
        Ingredients.objects.bulk_create([
            Ingredients(
                recipe=snapshot,
                **{field: getattr(item, field) for field in INGREDIENT_FIELDS},
            )
            for item in source_recipe.ingredients.all()
        ])
        post.save(update_fields=["updated_at"])
        return False
