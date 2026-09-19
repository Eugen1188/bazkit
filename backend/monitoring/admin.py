from django.contrib import admin
from django.utils import timezone

from .models import OperationalIssue


@admin.register(OperationalIssue)
class OperationalIssueAdmin(admin.ModelAdmin):
    list_display = (
        "source", "level", "message", "occurrences", "last_seen", "resolved_at",
    )
    list_filter = ("source", "level", "resolved_at")
    search_fields = ("message", "fingerprint")
    readonly_fields = (
        "fingerprint", "occurrences", "first_seen", "last_seen", "last_alerted_at",
    )
    actions = ("mark_resolved", "reopen")

    @admin.action(description="Als gelöst markieren")
    def mark_resolved(self, request, queryset):
        queryset.update(resolved_at=timezone.now())

    @admin.action(description="Wieder öffnen")
    def reopen(self, request, queryset):
        queryset.update(resolved_at=None)
