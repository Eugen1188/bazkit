from django.db import transaction

from django.db.models import Q

from rest_framework import status

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response

from rest_framework.views import APIView

from lists.models import (
    SavedList,
    SavedListItem,
)

from recipes.models import (
    Ingredients,
    Recipe,
)

from .models import (
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityRating,
)

from .serializers import (
    CommunityCommentSerializer,
    CommunityCreatePostSerializer,
    CommunityPostSerializer,
    CommunityRatingSerializer,
    CommunityUpdatePostSerializer,
)
from .snapshots import clone_recipe, clone_saved_list, delete_post_snapshot


class CommunityPostListCreateAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        queryset = (
            CommunityPost.objects
            .select_related(
                "author",
                "recipe",
                "saved_list"
            )
            .prefetch_related(
                "recipe__ingredients",
                "saved_list__items",
                "comments",
                "likes",
                "ratings"
            )
        )

        post_type = (
            request.query_params
            .get(
                "type",
                ""
            )
            .strip()
        )

        search = (
            request.query_params
            .get(
                "search",
                ""
            )
            .strip()
        )

        if post_type in [
            "recipe",
            "list",
            "thread",
        ]:
            queryset = queryset.filter(
                post_type=post_type
            )

        if search:

            queryset = queryset.filter(
                Q(
                    title__icontains=search
                )
                |
                Q(
                    content__icontains=search
                )
                |
                Q(
                    recipe__name__icontains=search
                )
                |
                Q(
                    recipe__description__icontains=
                        search
                )
                |
                Q(
                    saved_list__title__icontains=
                        search
                )
            )

        serializer = CommunityPostSerializer(
            queryset,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )

    def post(
        self,
        request
    ):

        serializer = (
            CommunityCreatePostSerializer(
                data=request.data,
                context={
                    "request": request
                }
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        post = serializer.save()

        return Response(
            CommunityPostSerializer(
                post,
                context={
                    "request": request
                }
            ).data,
            status=status.HTTP_201_CREATED
        )


class CommunityPostDetailAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get_object(
        self,
        pk
    ):

        return (
            CommunityPost.objects
            .select_related(
                "author",
                "recipe",
                "saved_list"
            )
            .prefetch_related(
                "recipe__ingredients",
                "saved_list__items",
                "comments__author",
                "likes",
                "ratings"
            )
            .filter(
                id=pk
            )
            .first()
        )

    def get(
        self,
        request,
        pk
    ):

        post = self.get_object(
            pk
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        return Response(
            CommunityPostSerializer(
                post,
                context={
                    "request": request
                }
            ).data
        )

    def patch(self, request, pk):
        post = self.get_object(pk)
        if not post or post.author_id != request.user.id:
            return Response(
                {"detail": "Beitrag nicht gefunden oder keine Berechtigung."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CommunityUpdatePostSerializer(
            post,
            data=request.data,
            partial=True,
            context={"post": post},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        post = self.get_object(pk)
        return Response(
            CommunityPostSerializer(post, context={"request": request}).data
        )

    @transaction.atomic
    def delete(
        self,
        request,
        pk
    ):

        post = (
            CommunityPost.objects
            .filter(
                id=pk,
                author=request.user
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden "
                        "oder keine Berechtigung."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        delete_post_snapshot(post)

        return Response(
            status=
                status.HTTP_204_NO_CONTENT
        )


class CommunityCommentsAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        post_id
    ):

        post = (
            CommunityPost.objects
            .filter(
                id=post_id
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        comments = (
            post.comments
            .select_related(
                "author"
            )
            .all()
        )

        return Response(
            CommunityCommentSerializer(
                comments,
                many=True
            ).data
        )

    def post(
        self,
        request,
        post_id
    ):

        post = (
            CommunityPost.objects
            .filter(
                id=post_id
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        serializer = (
            CommunityCommentSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        comment = serializer.save(
            post=post,
            author=request.user
        )

        return Response(
            CommunityCommentSerializer(
                comment
            ).data,
            status=
                status.HTTP_201_CREATED
        )


class CommunityCommentDetailAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        comment_id
    ):

        comment = (
            CommunityComment.objects
            .filter(
                id=comment_id,
                author=request.user
            )
            .first()
        )

        if not comment:

            return Response(
                {
                    "detail":
                        "Kommentar nicht gefunden "
                        "oder keine Berechtigung."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        comment.delete()

        return Response(
            status=
                status.HTTP_204_NO_CONTENT
        )


class CommunityLikeAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        post_id
    ):

        post = (
            CommunityPost.objects
            .filter(
                id=post_id
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        like = (
            CommunityLike.objects
            .filter(
                post=post,
                user=request.user
            )
            .first()
        )

        if like:

            like.delete()

            liked = False

        else:

            CommunityLike.objects.create(
                post=post,
                user=request.user
            )

            liked = True

        return Response(
            {
                "liked":
                    liked,

                "like_count":
                    post.likes.count()
            }
        )


class CommunityRatingAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        post_id
    ):

        post = (
            CommunityPost.objects
            .filter(
                id=post_id
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        if (
            post.post_type
            ==
            CommunityPost.POST_TYPE_THREAD
        ):

            return Response(
                {
                    "detail":
                        "Diskussionen können "
                        "nicht bewertet werden."
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )

        serializer = (
            CommunityRatingSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        rating, _ = (
            CommunityRating.objects
            .update_or_create(
                post=post,
                user=request.user,
                defaults={
                    "value":
                        serializer
                        .validated_data[
                            "value"
                        ]
                }
            )
        )

        serializer = (
            CommunityPostSerializer(
                post,
                context={
                    "request": request
                }
            )
        )

        return Response(
            {
                "rating":
                    rating.value,

                "rating_average":
                    serializer.data[
                        "rating_average"
                    ],

                "rating_count":
                    serializer.data[
                        "rating_count"
                    ]
            }
        )


class CommunityShareOptionsAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        recipes = (
            Recipe.objects
            .filter(
                user=request.user,
                is_community_snapshot=False,
            )
            .order_by(
                "-created_at"
            )
            .values(
                "id",
                "name"
            )
        )

        saved_lists = (
            SavedList.objects
            .filter(
                user=request.user,
                is_community_snapshot=False,
            )
            .order_by(
                "-created_at"
            )
            .values(
                "id",
                "title"
            )
        )

        return Response(
            {
                "recipes":
                    list(recipes),

                "saved_lists":
                    list(saved_lists)
            }
        )


class CommunityCopyPostAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    @transaction.atomic
    def post(
        self,
        request,
        post_id
    ):

        post = (
            CommunityPost.objects
            .select_related(
                "recipe",
                "saved_list"
            )
            .prefetch_related(
                "recipe__ingredients",
                "saved_list__items"
            )
            .filter(
                id=post_id
            )
            .first()
        )

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        if (
            post.post_type
            ==
            CommunityPost.POST_TYPE_RECIPE
            and
            post.recipe
        ):

            recipe = clone_recipe(post.recipe, request.user)

            return Response(
                {
                    "type":
                        "recipe",

                    "id":
                        recipe.id,

                    "detail":
                        "Rezept wurde zu deinen "
                        "Rezepten hinzugefügt."
                },
                status=
                    status.HTTP_201_CREATED
            )

        if (
            post.post_type
            ==
            CommunityPost.POST_TYPE_LIST
            and
            post.saved_list
        ):

            saved_list = clone_saved_list(post.saved_list, request.user)

            return Response(
                {
                    "type":
                        "list",

                    "id":
                        saved_list.id,

                    "detail":
                        "Liste wurde zu deinen "
                        "gespeicherten Listen hinzugefügt."
                },
                status=
                    status.HTTP_201_CREATED
            )

        return Response(
            {
                "detail":
                    "Dieser Beitrag kann "
                    "nicht übernommen werden."
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )
