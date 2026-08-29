from django.db import migrations


def backfill_recipe_snapshot_images(apps, schema_editor):
    CommunityPost = apps.get_model("community", "CommunityPost")
    Recipe = apps.get_model("recipes", "Recipe")

    posts = (
        CommunityPost.objects
        .filter(
            post_type="recipe",
            recipe__isnull=False,
            recipe__image_key="",
            source_recipe__isnull=False,
        )
        .exclude(source_recipe__image_key="")
        .values_list("recipe_id", "source_recipe__image_key")
    )

    for recipe_id, image_key in posts.iterator():
        Recipe.objects.filter(pk=recipe_id, image_key="").update(image_key=image_key)


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0003_detach_existing_posts"),
        ("recipes", "0008_recipe_image_key"),
    ]

    operations = [
        migrations.RunPython(backfill_recipe_snapshot_images, migrations.RunPython.noop),
    ]
