import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0011_repair_cooking_wines"),
    ]

    operations = [
        migrations.CreateModel(
            name="IngredientSearchMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("normalized_query", models.CharField(max_length=100)),
                ("display_query", models.CharField(max_length=100)),
                ("context", models.CharField(choices=[("recipe_create", "Rezept erstellen"), ("recipe_edit", "Rezept bearbeiten"), ("shopping_list", "Einkaufsliste"), ("saved_list", "Gespeicherte Liste")], max_length=30)),
                ("search_count", models.PositiveIntegerField(default=0)),
                ("zero_result_count", models.PositiveIntegerField(default=0)),
                ("selection_count", models.PositiveIntegerField(default=0)),
                ("last_result_count", models.PositiveSmallIntegerField(default=0)),
                ("last_selected_rank", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("selection_counts", models.JSONField(blank=True, default=dict)),
                ("review_status", models.CharField(choices=[("open", "Offen"), ("resolved", "Gelöst"), ("ignored", "Ignoriert")], db_index=True, default="open", max_length=20)),
                ("review_note", models.CharField(blank=True, max_length=250)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("last_selected_product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ingredient_search_metrics", to="products.product")),
            ],
            options={
                "ordering": ["-zero_result_count", "-search_count", "normalized_query"],
                "indexes": [models.Index(fields=["review_status", "-zero_result_count"], name="ingredient_search_gap_idx")],
                "constraints": [models.UniqueConstraint(fields=("normalized_query", "context"), name="unique_ingredient_search_metric")],
            },
        ),
    ]
