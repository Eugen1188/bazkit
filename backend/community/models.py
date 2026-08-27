from django.conf import settings

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)

from django.db import models

from lists.models import SavedList

from recipes.models import Recipe


class CommunityPost(models.Model):

    POST_TYPE_RECIPE = "recipe"
    POST_TYPE_LIST = "list"
    POST_TYPE_THREAD = "thread"

    POST_TYPE_CHOICES = [
        (
            POST_TYPE_RECIPE,
            "Rezept"
        ),
        (
            POST_TYPE_LIST,
            "Einkaufsliste"
        ),
        (
            POST_TYPE_THREAD,
            "Diskussion"
        ),
    ]

    THREAD_CATEGORY_CHOICES = [
        (
            "cooking",
            "Kochen"
        ),
        (
            "shopping",
            "Einkaufen"
        ),
        (
            "nutrition",
            "Ernährung"
        ),
        (
            "saving",
            "Sparen"
        ),
        (
            "products",
            "Lebensmittel & Produkte"
        ),
        (
            "appliances",
            "Küchengeräte"
        ),
        (
            "other",
            "Sonstiges"
        ),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts"
    )

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="community_posts"
    )

    saved_list = models.ForeignKey(
        SavedList,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="community_posts"
    )

    source_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_community_posts",
    )

    source_saved_list = models.ForeignKey(
        SavedList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_community_posts",
    )

    title = models.CharField(
        max_length=160,
        blank=True
    )

    content = models.TextField(
        blank=True
    )

    thread_category = models.CharField(
        max_length=30,
        choices=THREAD_CATEGORY_CHOICES,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):

        if self.post_type == self.POST_TYPE_RECIPE:
            return (
                self.recipe.name
                if self.recipe
                else "Rezept"
            )

        if self.post_type == self.POST_TYPE_LIST:
            return (
                self.saved_list.title
                if self.saved_list
                else "Einkaufsliste"
            )

        return (
            self.title
            or "Diskussion"
        )


class CommunityComment(models.Model):

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments"
    )

    content = models.TextField(
        max_length=3000
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "created_at"
        ]

    def __str__(self):
        return (
            f"Kommentar #{self.id}"
        )


class CommunityLike(models.Model):

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="likes"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_likes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "post",
                    "user"
                ],
                name="unique_community_like"
            )
        ]

    def __str__(self):
        return (
            f"{self.user_id} → "
            f"{self.post_id}"
        )


class CommunityRating(models.Model):

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_ratings"
    )

    value = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "post",
                    "user"
                ],
                name="unique_community_rating"
            )
        ]

    def __str__(self):
        return (
            f"{self.value}/5"
        )
