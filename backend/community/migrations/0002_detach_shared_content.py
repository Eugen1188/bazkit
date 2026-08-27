from django.db import migrations, models
import django.db.models.deletion


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
    ]