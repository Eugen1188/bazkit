from django.db import models


class OperationalIssue(models.Model):
    class Source(models.TextChoices):
        BACKEND = "backend", "Backend"
        EMAIL = "email", "E-Mail"
        BROWSER = "browser", "Browser"

    class Level(models.TextChoices):
        ERROR = "error", "Fehler"
        CRITICAL = "critical", "Kritisch"

    fingerprint = models.CharField(max_length=64, unique=True)
    source = models.CharField(max_length=16, choices=Source.choices)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.ERROR)
    message = models.CharField(max_length=500)
    details = models.JSONField(default=dict, blank=True)
    occurrences = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    last_alerted_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_seen"]
        indexes = [
            models.Index(
                fields=["source", "resolved_at", "-last_seen"],
                name="monitoring_issue_state_idx",
            ),
        ]

    def __str__(self):
        return f"{self.get_source_display()}: {self.message}"
