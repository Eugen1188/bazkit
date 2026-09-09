from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0004_backfill_recipe_snapshot_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="communityrating",
            name="comment",
            field=models.TextField(blank=True, default="", max_length=1000),
        ),
    ]
