from django.contrib import admin

from .models import (
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityRating,
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