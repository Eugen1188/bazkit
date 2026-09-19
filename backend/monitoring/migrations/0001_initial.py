from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OperationalIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fingerprint", models.CharField(max_length=64, unique=True)),
                ("source", models.CharField(choices=[("backend", "Backend"), ("email", "E-Mail"), ("browser", "Browser")], max_length=16)),
                ("level", models.CharField(choices=[("error", "Fehler"), ("critical", "Kritisch")], default="error", max_length=16)),
                ("message", models.CharField(max_length=500)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("occurrences", models.PositiveIntegerField(default=1)),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("last_alerted_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-last_seen"]},
        ),
        migrations.AddIndex(
            model_name="operationalissue",
            index=models.Index(fields=["source", "resolved_at", "-last_seen"], name="monitoring_issue_state_idx"),
        ),
    ]
