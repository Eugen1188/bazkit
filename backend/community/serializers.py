from django.db import transaction
from django.db.models import Avg

from rest_framework import serializers

from lists.models import (
    SavedList,
    SavedListItem,
)

from recipes.models import (
    Ingredients,
    Recipe,
)
from recipes.storage import get_recipe_image_url

from .models import (
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityRating,
)
from .snapshots import clone_recipe, clone_saved_list


class CommunityAuthorSerializer(
    serializers.Serializer
):

    id = serializers.IntegerField(
        read_only=True
    )

    name = serializers.SerializerMethodField()

    def get_name(
        self,
        obj
    ):

        return (
            obj.first_name
            or
            obj.username
        )


class CommunityIngredientSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Ingredients

        fields = [
            "id",
            "name",
            "quantity",
            "unit",
        ]


class CommunityRecipeSerializer(
    serializers.ModelSerializer
):

    image_url = serializers.SerializerMethodField()

    ingredients = (
        CommunityIngredientSerializer(
            many=True,
            read_only=True
        )
    )

    class Meta:

        model = Recipe

        fields = [
            "id",
            "name",
            "description",
            "servings",
            "preparation_time",
            "category",
            "instructions",
            "notes",
            "image_url",
            "image_position_x",
            "image_position_y",
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "fiber",
            "estimated_price",
            "ingredients",
            "created_at",
        ]

    def get_image_url(self, obj):
        return get_recipe_image_url(obj.image_key)


class CommunitySavedListItemSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = SavedListItem

        fields = [
            "id",
            "name",
            "quantity",
            "unit",
            "note",
        ]


class CommunitySavedListSerializer(
    serializers.ModelSerializer
):

    items = (
        CommunitySavedListItemSerializer(
            many=True,
            read_only=True
        )
    )

    item_count = (
        serializers.SerializerMethodField()
    )

    class Meta:

        model = SavedList

        fields = [
            "id",
            "title",
            "created_at",
            "item_count",
            "items",
        ]

    def get_item_count(
        self,
        obj
    ):

        return obj.items.count()


class CommunityRecipeListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image_url",
            "image_position_x",
            "image_position_y",
        ]

    def get_image_url(self, obj):
        return get_recipe_image_url(obj.image_key)


class CommunitySavedListListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = SavedList
        fields = ["id", "title", "item_count"]

    def get_item_count(self, obj):
        return obj.items.count()


class CommunityCommentSerializer(
    serializers.ModelSerializer
):

    author = (
        CommunityAuthorSerializer(
            read_only=True
        )
    )

    class Meta:

        model = CommunityComment

        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
        ]


class CommunityPostSerializer(
    serializers.ModelSerializer
):

    author = (
        CommunityAuthorSerializer(
            read_only=True
        )
    )

    recipe = (
        CommunityRecipeSerializer(
            read_only=True
        )
    )

    saved_list = (
        CommunitySavedListSerializer(
            read_only=True
        )
    )

    display_title = (
        serializers.SerializerMethodField()
    )

    display_description = (
        serializers.SerializerMethodField()
    )

    comment_count = (
        serializers.SerializerMethodField()
    )

    like_count = (
        serializers.SerializerMethodField()
    )

    liked_by_me = (
        serializers.SerializerMethodField()
    )

    rating_average = (
        serializers.SerializerMethodField()
    )

    rating_count = (
        serializers.SerializerMethodField()
    )

    my_rating = (
        serializers.SerializerMethodField()
    )

    is_author = serializers.SerializerMethodField()

    class Meta:

        model = CommunityPost

        fields = [
            "id",
            "post_type",
            "author",
            "title",
            "content",
            "thread_category",
            "recipe",
            "saved_list",
            "display_title",
            "display_description",
            "comment_count",
            "like_count",
            "liked_by_me",
            "rating_average",
            "rating_count",
            "my_rating",
            "is_author",
            "created_at",
            "updated_at",
        ]

    def get_display_title(
        self,
        obj
    ):

        if (
            obj.post_type
            ==
            CommunityPost.POST_TYPE_RECIPE
            and
            obj.recipe
        ):
            return obj.recipe.name

        if (
            obj.post_type
            ==
            CommunityPost.POST_TYPE_LIST
            and
            obj.saved_list
        ):
            return obj.saved_list.title

        return obj.title

    def get_display_description(
        self,
        obj
    ):

        if (
            obj.post_type
            ==
            CommunityPost.POST_TYPE_RECIPE
            and
            obj.recipe
        ):
            return (
                obj.recipe.description
                or
                obj.recipe.instructions[:180]
            )

        if (
            obj.post_type
            ==
            CommunityPost.POST_TYPE_LIST
            and
            obj.saved_list
        ):

            return (
                f"{obj.saved_list.items.count()} "
                f"Produkte"
            )

        return obj.content[:220]

    def get_comment_count(
        self,
        obj
    ):

        if hasattr(obj, "annotated_comment_count"):
            return obj.annotated_comment_count

        return obj.comments.count()

    def get_like_count(
        self,
        obj
    ):

        if hasattr(obj, "annotated_like_count"):
            return obj.annotated_like_count

        return obj.likes.count()

    def get_liked_by_me(
        self,
        obj
    ):

        if hasattr(obj, "annotated_liked_by_me"):
            return obj.annotated_liked_by_me

        request = self.context.get(
            "request"
        )

        if (
            not request
            or
            not request.user.is_authenticated
        ):
            return False

        return obj.likes.filter(
            user=request.user
        ).exists()

    def get_rating_average(
        self,
        obj
    ):

        if hasattr(obj, "annotated_rating_average"):
            average = obj.annotated_rating_average
        else:
            result = (
                obj.ratings
                .aggregate(
                    average=Avg(
                        "value"
                    )
                )
            )

            average = result.get(
                "average"
            )

        if average is None:
            return None

        return round(
            float(average),
            1
        )

    def get_rating_count(
        self,
        obj
    ):

        if hasattr(obj, "annotated_rating_count"):
            return obj.annotated_rating_count

        return obj.ratings.count()

    def get_my_rating(
        self,
        obj
    ):

        if hasattr(obj, "annotated_my_rating"):
            return obj.annotated_my_rating

        request = self.context.get(
            "request"
        )

        if (
            not request
            or
            not request.user.is_authenticated
        ):
            return None

        rating = (
            obj.ratings
            .filter(
                user=request.user
            )
            .first()
        )

        if not rating:
            return None

        return rating.value

    def get_is_author(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.author_id == request.user.id
        )


class CommunityPostListSerializer(CommunityPostSerializer):
    recipe = CommunityRecipeListSerializer(read_only=True)
    saved_list = CommunitySavedListListSerializer(read_only=True)


class CommunityCreatePostSerializer(
    serializers.Serializer
):

    post_type = serializers.ChoiceField(
        choices=[
            CommunityPost.POST_TYPE_RECIPE,
            CommunityPost.POST_TYPE_LIST,
            CommunityPost.POST_TYPE_THREAD,
        ]
    )

    recipe_id = serializers.IntegerField(
        required=False
    )

    saved_list_id = serializers.IntegerField(
        required=False
    )

    title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=160
    )

    content = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000
    )

    thread_category = (
        serializers.ChoiceField(
            choices=[
                choice[0]
                for choice
                in (
                    CommunityPost
                    .THREAD_CATEGORY_CHOICES
                )
            ],
            required=False,
            allow_blank=True
        )
    )

    def validate(
        self,
        attrs
    ):

        request = self.context[
            "request"
        ]

        post_type = attrs[
            "post_type"
        ]

        if (
            post_type
            ==
            CommunityPost.POST_TYPE_RECIPE
        ):

            recipe_id = attrs.get(
                "recipe_id"
            )

            if not recipe_id:
                raise serializers.ValidationError(
                    {
                        "recipe_id":
                            "Bitte wähle ein Rezept aus."
                    }
                )

            recipe = (
                Recipe.objects
                .filter(
                    id=recipe_id,
                    user=request.user,
                    is_community_snapshot=False,
                )
                .first()
            )

            if not recipe:
                raise serializers.ValidationError(
                    {
                        "recipe_id":
                            "Rezept nicht gefunden."
                    }
                )

            if (
                CommunityPost.objects
                .filter(
                    author=request.user,
                    source_recipe=recipe,
                    post_type=
                        CommunityPost
                        .POST_TYPE_RECIPE
                )
                .exists()
            ):

                raise serializers.ValidationError(
                    {
                        "recipe_id":
                            "Dieses Rezept ist bereits "
                            "in der Community veröffentlicht."
                    }
                )

            attrs[
                "recipe_object"
            ] = recipe

        elif (
            post_type
            ==
            CommunityPost.POST_TYPE_LIST
        ):

            saved_list_id = attrs.get(
                "saved_list_id"
            )

            if not saved_list_id:
                raise serializers.ValidationError(
                    {
                        "saved_list_id":
                            "Bitte wähle eine Liste aus."
                    }
                )

            saved_list = (
                SavedList.objects
                .filter(
                    id=saved_list_id,
                    user=request.user,
                    is_community_snapshot=False,
                )
                .first()
            )

            if not saved_list:
                raise serializers.ValidationError(
                    {
                        "saved_list_id":
                            "Liste nicht gefunden."
                    }
                )

            if (
                CommunityPost.objects
                .filter(
                    author=request.user,
                    source_saved_list=saved_list,
                    post_type=
                        CommunityPost
                        .POST_TYPE_LIST
                )
                .exists()
            ):

                raise serializers.ValidationError(
                    {
                        "saved_list_id":
                            "Diese Liste ist bereits "
                            "in der Community veröffentlicht."
                    }
                )

            attrs[
                "saved_list_object"
            ] = saved_list

        elif (
            post_type
            ==
            CommunityPost.POST_TYPE_THREAD
        ):

            title = (
                attrs.get(
                    "title",
                    ""
                )
                .strip()
            )

            content = (
                attrs.get(
                    "content",
                    ""
                )
                .strip()
            )

            if not title:
                raise serializers.ValidationError(
                    {
                        "title":
                            "Bitte gib einen Titel ein."
                    }
                )

            if not content:
                raise serializers.ValidationError(
                    {
                        "content":
                            "Bitte beschreibe dein Thema."
                    }
                )

        return attrs

    @transaction.atomic
    def create(
        self,
        validated_data
    ):

        request = self.context[
            "request"
        ]

        post_type = validated_data[
            "post_type"
        ]

        source_recipe = validated_data.get("recipe_object")
        source_saved_list = validated_data.get("saved_list_object")
        recipe = (
            clone_recipe(source_recipe, request.user, community_snapshot=True)
            if source_recipe is not None
            else None
        )
        saved_list = (
            clone_saved_list(source_saved_list, request.user, community_snapshot=True)
            if source_saved_list is not None
            else None
        )

        return CommunityPost.objects.create(
            author=request.user,

            post_type=post_type,

            recipe=recipe,

            source_recipe=source_recipe,

            saved_list=saved_list,

            source_saved_list=source_saved_list,

            title=validated_data.get(
                "title",
                ""
            ),

            content=validated_data.get(
                "content",
                ""
            ),

            thread_category=
                validated_data.get(
                    "thread_category",
                    ""
                )
        )


class CommunityUpdatePostSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=160)
    content = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    thread_category = serializers.ChoiceField(
        choices=[choice[0] for choice in CommunityPost.THREAD_CATEGORY_CHOICES],
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        post = self.context["post"]
        if post.post_type == CommunityPost.POST_TYPE_THREAD:
            title = attrs.get("title", post.title).strip()
            content = attrs.get("content", post.content).strip()
            if not title:
                raise serializers.ValidationError({"title": "Bitte gib einen Titel ein."})
            if not content:
                raise serializers.ValidationError({"content": "Bitte beschreibe dein Thema."})
            attrs["title"] = title
            attrs["content"] = content
        return attrs

    def update(self, instance, validated_data):
        for field in ("title", "content", "thread_category"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        return instance


class CommunityRatingSerializer(
    serializers.Serializer
):

    value = serializers.IntegerField(
        min_value=1,
        max_value=5
    )
