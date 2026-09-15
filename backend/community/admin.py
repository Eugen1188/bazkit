from django.contrib import admin

from .models import (
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityRating,
    CommunityReport,
)


@admin.register(
    CommunityPost
)
class CommunityPostAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "post_type",
        "author",
        "title",
        "created_at",
    ]

    list_filter = [
        "post_type",
        "created_at",
    ]

    search_fields = [
        "title",
        "content",
        "author__username",
        "author__first_name",
    ]


@admin.register(
    CommunityComment
)
class CommunityCommentAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "post",
        "author",
        "created_at",
    ]


@admin.register(
    CommunityLike
)
class CommunityLikeAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "post",
        "user",
        "created_at",
    ]


@admin.register(
    CommunityRating
)
class CommunityRatingAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "post",
        "user",
        "value",
        "created_at",
    ]


@admin.register(CommunityReport)
class CommunityReportAdmin(admin.ModelAdmin):
    list_display = (
        "id", "post", "reporter", "reason", "status", "created_at",
    )
    list_filter = ("status", "reason", "created_at")
    list_editable = ("status",)
    list_select_related = ("post", "reporter")
    search_fields = (
        "post__title", "post__content", "reporter__username",
        "reporter__email", "details", "moderator_note",
    )
    readonly_fields = ("post", "reporter", "reason", "details", "created_at", "updated_at")
    actions = ("mark_reviewing", "mark_resolved", "mark_dismissed")

    @admin.action(description="Ausgewählte Meldungen in Prüfung setzen")
    def mark_reviewing(self, request, queryset):
        queryset.update(status="reviewing")

    @admin.action(description="Ausgewählte Meldungen als erledigt markieren")
    def mark_resolved(self, request, queryset):
        queryset.update(status="resolved")

    @admin.action(description="Ausgewählte Meldungen abweisen")
    def mark_dismissed(self, request, queryset):
        queryset.update(status="dismissed")
