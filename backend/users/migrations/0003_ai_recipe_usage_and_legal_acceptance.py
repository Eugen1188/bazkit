from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_usersettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="terms_version",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="premium_active",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="AIRecipeUsage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("period_start", models.DateField()),
                ("generations_used", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_recipe_usage",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
