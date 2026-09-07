import django.utils.timezone
from django.db import migrations, models


def mark_existing_users_as_verified(apps, schema_editor):
    user_model = apps.get_model("users", "User")
    user_model.objects.filter(email_verified_at__isnull=True).update(
        email_verified_at=django.utils.timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_ai_recipe_usage_and_legal_acceptance"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar_key",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_token",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="pending_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.RunPython(
            mark_existing_users_as_verified,
            migrations.RunPython.noop,
        ),
    ]
