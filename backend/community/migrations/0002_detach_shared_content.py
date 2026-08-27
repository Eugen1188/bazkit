from django.db import migrations, models
import django.db.models.deletion


RECIPE_FIELDS = (
    "name", "description", "servings", "preparation_time", "category",
    "instructions", "notes", "calories", "protein", "carbohydrates",
    "fat", "fiber", "estimated_price",
)
INGREDIENT_FIELDS = (
    "product_id", "name", "quantity", "unit", "estimated_price",
    "price_source", "price_currency", "price_date", "price_store",
    "price_sample_count", "price_min", "price_max", "package_price",
    "package_quantity", "package_unit",
)
LIST_ITEM_FIELDS = (
    "product_id", "name", "quantity", "unit", "note", "estimated_price",
    "price_source", "price_currency", "price_date", "price_store",
    "price_sample_count", "price_min", "price_max", "package_price",
    "package_quantity", "package_unit",
)


def detach_existing_posts(apps, schema_editor):
    CommunityPost = apps.get_model("community", "CommunityPost")
    Recipe = apps.get_model("recipes", "Recipe")
    Ingredients = apps.get_model("recipes", "Ingredients")
    SavedList = apps.get_model("lists", "SavedList")
    SavedListItem = apps.get_model("lists", "SavedListItem")

    for post in CommunityPost.objects.filter(post_type="recipe", recipe__isnull=False):
        source = Recipe.objects.get(pk=post.recipe_id)
        snapshot = Recipe.objects.create(
            user_id=post.author_id,
            is_community_snapshot=True,
            **{field: getattr(source, field) for field in RECIPE_FIELDS},
        )
        Ingredients.objects.bulk_create([
            Ingredients(
                recipe_id=snapshot.id,
                **{field: getattr(item, field) for field in INGREDIENT_FIELDS},
            )
            for item in Ingredients.objects.filter(recipe_id=source.id)
        ])
        post.source_recipe_id = source.id
        post.recipe_id = snapshot.id
        post.save(update_fields=["source_recipe", "recipe"])

    for post in CommunityPost.objects.filter(post_type="list", saved_list__isnull=False):
        source = SavedList.objects.get(pk=post.saved_list_id)
        snapshot = SavedList.objects.create(
            user_id=post.author_id,
            title=source.title,
            is_community_snapshot=True,
        )
        SavedListItem.objects.bulk_create([
            SavedListItem(
                saved_list_id=snapshot.id,
                **{field: getattr(item, field) for field in LIST_ITEM_FIELDS},
            )
            for item in SavedListItem.objects.filter(saved_list_id=source.id)
        ])
        post.source_saved_list_id = source.id
        post.saved_list_id = snapshot.id
        post.save(update_fields=["source_saved_list", "saved_list"])


def restore_original_links(apps, schema_editor):
    CommunityPost = apps.get_model("community", "CommunityPost")
    Recipe = apps.get_model("recipes", "Recipe")
    SavedList = apps.get_model("lists", "SavedList")

    for post in CommunityPost.objects.filter(source_recipe__isnull=False):
        snapshot_id = post.recipe_id
        post.recipe_id = post.source_recipe_id
        post.save(update_fields=["recipe"])
        Recipe.objects.filter(pk=snapshot_id, is_community_snapshot=True).delete()

    for post in CommunityPost.objects.filter(source_saved_list__isnull=False):
        snapshot_id = post.saved_list_id
        post.saved_list_id = post.source_saved_list_id
        post.save(update_fields=["saved_list"])
        SavedList.objects.filter(pk=snapshot_id, is_community_snapshot=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0001_initial"),
        ("lists", "0006_savedlist_is_community_snapshot"),
        ("recipes", "0007_recipe_is_community_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="communitypost",
            name="source_recipe",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="published_community_posts",
                to="recipes.recipe",
            ),
        ),
        migrations.AddField(
            model_name="communitypost",
            name="source_saved_list",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="published_community_posts",
                to="lists.savedlist",
            ),
        ),
        migrations.RunPython(detach_existing_posts, restore_original_links),
    ]
