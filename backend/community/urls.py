from django.urls import path

from .views import (
    CommunityCommentDetailAPIView,
    CommunityCommentsAPIView,
    CommunityCopyPostAPIView,
    CommunityLikeAPIView,
    CommunityPostDetailAPIView,
    CommunityPostListCreateAPIView,
    CommunityRatingAPIView,
    CommunityShareOptionsAPIView,
)


urlpatterns = [

    path(
        "posts/",
        CommunityPostListCreateAPIView.as_view(),
        name="community-posts"
    ),

    path(
        "posts/<int:pk>/",
        CommunityPostDetailAPIView.as_view(),
        name="community-post-detail"
    ),

    path(
        "posts/<int:post_id>/comments/",
        CommunityCommentsAPIView.as_view(),
        name="community-comments"
    ),

    path(
        "comments/<int:comment_id>/",
        CommunityCommentDetailAPIView.as_view(),
        name="community-comment-detail"
    ),

    path(
        "posts/<int:post_id>/like/",
        CommunityLikeAPIView.as_view(),
        name="community-like"
    ),

    path(
        "posts/<int:post_id>/rating/",
        CommunityRatingAPIView.as_view(),
        name="community-rating"
    ),

    path(
        "posts/<int:post_id>/copy/",
        CommunityCopyPostAPIView.as_view(),
        name="community-copy"
    ),

    path(
        "share-options/",
        CommunityShareOptionsAPIView.as_view(),
        name="community-share-options"
    ),

]