from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lists", "0005_list_item_price_snapshots"),
    ]

    operations = [
        migrations.AddField(
            model_name="savedlist",
            name="is_community_snapshot",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
