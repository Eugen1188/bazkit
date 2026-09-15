import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0005_communityrating_comment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunityReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(choices=[("spam", "Spam oder Werbung"), ("abuse", "Beleidigung oder Belästigung"), ("dangerous", "Gefährlicher oder irreführender Inhalt"), ("copyright", "Urheberrechtsverletzung"), ("other", "Anderer Grund")], max_length=20)),
                ("details", models.TextField(blank=True, max_length=1000)),
                ("status", models.CharField(choices=[("open", "Offen"), ("reviewing", "In Prüfung"), ("resolved", "Erledigt"), ("dismissed", "Abgewiesen")], db_index=True, default="open", max_length=20)),
                ("moderator_note", models.TextField(blank=True, max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="community.communitypost")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="communityreport",
            constraint=models.UniqueConstraint(fields=("post", "reporter"), name="unique_community_report"),
        ),
    ]
