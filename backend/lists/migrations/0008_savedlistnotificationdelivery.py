import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lists", "0007_saved_list_collaboration"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedListNotificationDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_sent_at", models.DateTimeField(blank=True, null=True)),
                ("saved_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_deliveries", to="lists.savedlist")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_list_notification_deliveries", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="savedlistnotificationdelivery",
            constraint=models.UniqueConstraint(fields=("saved_list", "user"), name="unique_saved_list_notification_delivery"),
        ),
    ]
