from datetime import timedelta

from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from django.db.models import Avg, Count, Exists, IntegerField, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.functions import Coalesce

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
    CommunityBlock,
    CommunityLike,
    CommunityPost,
    CommunityRating,
    CommunityReport,
)
from .throttles import (
    CommunityBlockThrottle,
    CommunityCommentWriteThrottle,
    CommunityInteractionThrottle,
    CommunityPostWriteThrottle,
    CommunityReportThrottle,
)

from .serializers import (
    CommunityCommentSerializer,
    CommunityCreatePostSerializer,
    CommunityPostDetailSerializer,
    CommunityPostListSerializer,
    CommunityPostSerializer,
    CommunityRatingReviewSerializer,
    CommunityRatingSerializer,
    CommunityUpdatePostSerializer,
)
from .snapshots import clone_recipe, clone_saved_list, delete_post_snapshot
from users.storage import get_avatar_url


User = get_user_model()


class WriteThrottleMixin:
    write_throttle_class = None

    def get_throttles(self):
        if self.request.method in {"POST", "PUT", "PATCH", "DELETE"} and self.write_throttle_class:
            return [self.write_throttle_class()]
        return []


def blocked_user_ids(user):
    outgoing = CommunityBlock.objects.filter(blocker=user).values_list("blocked_id", flat=True)
    incoming = CommunityBlock.objects.filter(blocked=user).values_list("blocker_id", flat=True)
    return set(outgoing).union(incoming)


def community_post_queryset(request, *, include_content=False):
    excluded_authors = blocked_user_ids(request.user)

    def related_count(model, user_field):
        counts = model.objects.filter(post_id=OuterRef("pk"))
        if excluded_authors:
            counts = counts.exclude(**{f"{user_field}__in": excluded_authors})
        counts = (
            counts
            .order_by()
            .values("post_id")
            .annotate(value=Count("id"))
            .values("value")[:1]
        )
        return Coalesce(
            Subquery(counts, output_field=IntegerField()),
            Value(0),
        )

    ratings = CommunityRating.objects.filter(post_id=OuterRef("pk"))
    if excluded_authors:
        ratings = ratings.exclude(user_id__in=excluded_authors)
    rating_average = (
        ratings.values("post_id")
        .annotate(value=Avg("value"))
        .values("value")[:1]
    )

    queryset = (
        CommunityPost.objects
        .select_related("author", "recipe", "saved_list")
        .annotate(
            annotated_comment_count=related_count(CommunityComment, "author_id"),
            annotated_like_count=related_count(CommunityLike, "user_id"),
            annotated_rating_count=related_count(CommunityRating, "user_id"),
            annotated_rating_average=Subquery(rating_average),
            annotated_liked_by_me=Exists(
                CommunityLike.objects.filter(
                    post_id=OuterRef("pk"),
                    user=request.user,
                )
            ),
            annotated_my_rating=Subquery(
                ratings.filter(user=request.user).values("value")[:1]
            ),
        )
    )

    if excluded_authors:
        queryset = queryset.exclude(author_id__in=excluded_authors)

    if include_content:
        return queryset.prefetch_related(
            "recipe__ingredients",
            "saved_list__items",
            Prefetch(
                "ratings",
                queryset=(
                    CommunityRating.objects.select_related("user")
                    .exclude(user_id__in=excluded_authors)
                    .order_by("-updated_at")
                ),
                to_attr="prefetched_ratings",
            ),
        )

    return queryset.prefetch_related("saved_list__items")


def visible_post(request, post_id, *, include_content=False):
    return (
        community_post_queryset(request, include_content=include_content)
        .filter(id=post_id)
        .first()
    )


class CommunityPostListCreateAPIView(
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityPostWriteThrottle

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        queryset = community_post_queryset(request)

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

        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except (TypeError, ValueError):
            offset = 0

        raw_limit = request.query_params.get("limit")
        if raw_limit is not None:
            try:
                limit = max(1, min(100, int(raw_limit)))
            except (TypeError, ValueError):
                limit = 20
            queryset = queryset[offset:offset + limit]

        serializer = CommunityPostListSerializer(
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
            CommunityPostDetailSerializer(
                post,
                context={
                    "request": request
                }
            ).data,
            status=status.HTTP_201_CREATED
        )


class CommunityPostDetailAPIView(
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityPostWriteThrottle

    permission_classes = [
        IsAuthenticated
    ]

    def get_object(
        self,
        request,
        pk
    ):

        return (
            community_post_queryset(request, include_content=True)
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
            request,
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
            CommunityPostDetailSerializer(
                post,
                context={
                    "request": request
                }
            ).data
        )

    def patch(self, request, pk):
        post = self.get_object(request, pk)
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
        post = self.get_object(request, pk)
        return Response(
            CommunityPostDetailSerializer(post, context={"request": request}).data
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


class CommunityReportAPIView(WriteThrottleMixin, APIView):
    permission_classes = [IsAuthenticated]
    write_throttle_class = CommunityReportThrottle

    def post(self, request, post_id):
        post = visible_post(request, post_id)
        if not post:
            return Response(
                {"detail": "Beitrag nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.author_id == request.user.id:
            return Response(
                {"detail": "Eigene Beiträge können nicht gemeldet werden."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = str(request.data.get("reason", "")).strip()
        valid_reasons = {value for value, _label in CommunityReport.REASON_CHOICES}
        if reason not in valid_reasons:
            return Response(
                {"reason": ["Bitte wähle einen gültigen Meldegrund aus."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        details = str(request.data.get("details", "")).strip()
        if len(details) > 1000:
            return Response(
                {"details": ["Die Beschreibung darf höchstens 1000 Zeichen lang sein."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report, created = CommunityReport.objects.update_or_create(
            post=post,
            reporter=request.user,
            defaults={
                "reason": reason,
                "details": details,
                "status": "open",
            },
        )
        return Response(
            {
                "detail": "Danke. Der Beitrag wurde zur Prüfung gemeldet.",
                "report_id": report.id,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CommunityCommentsAPIView(
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityCommentWriteThrottle

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        post_id
    ):

        post = visible_post(request, post_id)

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        excluded_authors = blocked_user_ids(request.user)
        comments = (
            post.comments
            .select_related(
                "author"
            )
            .exclude(author_id__in=excluded_authors)
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

        post = visible_post(request, post_id)

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

        normalized_content = serializer.validated_data["content"].strip()
        recently_posted = CommunityComment.objects.filter(
            post=post,
            author=request.user,
            content__iexact=normalized_content,
            created_at__gte=timezone.now() - timedelta(minutes=2),
        ).exists()
        if recently_posted:
            return Response(
                {"content": ["Dieser Kommentar wurde gerade bereits gesendet."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = serializer.save(
            post=post,
            author=request.user,
            content=normalized_content,
        )

        return Response(
            CommunityCommentSerializer(
                comment
            ).data,
            status=
                status.HTTP_201_CREATED
        )


class CommunityCommentDetailAPIView(
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityCommentWriteThrottle

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
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityInteractionThrottle

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        post_id
    ):

        post = visible_post(request, post_id)

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        if post.post_type == CommunityPost.POST_TYPE_RECIPE:
            return Response(
                {
                    "detail":
                        "Rezepte können nicht geliked werden. "
                        "Nutze stattdessen die Bewertung."
                },
                status=status.HTTP_400_BAD_REQUEST,
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
    WriteThrottleMixin,
    APIView
):

    write_throttle_class = CommunityInteractionThrottle

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        post_id
    ):

        post = visible_post(request, post_id)

        if not post:

            return Response(
                {
                    "detail":
                        "Beitrag nicht gefunden."
                },
                status=
                    status.HTTP_404_NOT_FOUND
            )

        if post.post_type != CommunityPost.POST_TYPE_RECIPE:

            return Response(
                {
                    "detail":
                        "Nur Rezepte können bewertet werden."
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
                        ],
                    "comment": serializer.validated_data["comment"],
                }
            )
        )

        post = visible_post(request, post_id)
        serializer = CommunityPostSerializer(post, context={"request": request})

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
                    ],

                "rating_comment": rating.comment,

                "review": CommunityRatingReviewSerializer(rating).data,
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

        post = visible_post(request, post_id, include_content=True)

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


class CommunityBlockedUsersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        blocks = (
            CommunityBlock.objects.filter(blocker=request.user)
            .select_related("blocked")
            .order_by("blocked__first_name", "blocked__username")
        )
        return Response([
            {
                "id": block.blocked_id,
                "name": block.blocked.first_name or block.blocked.username,
                "avatar_url": get_avatar_url(block.blocked.avatar_key),
                "blocked_at": block.created_at,
            }
            for block in blocks
        ])


class CommunityBlockAPIView(WriteThrottleMixin, APIView):
    permission_classes = [IsAuthenticated]
    write_throttle_class = CommunityBlockThrottle

    def post(self, request, user_id):
        if user_id == request.user.id:
            return Response(
                {"detail": "Du kannst dich nicht selbst blockieren."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        blocked_user = User.objects.filter(id=user_id, is_active=True).first()
        if not blocked_user:
            return Response(
                {"detail": "Nutzer nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        CommunityBlock.objects.get_or_create(
            blocker=request.user,
            blocked=blocked_user,
        )
        return Response({
            "detail": f"{blocked_user.first_name or blocked_user.username} wurde blockiert."
        })

    def delete(self, request, user_id):
        CommunityBlock.objects.filter(
            blocker=request.user,
            blocked_id=user_id,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
