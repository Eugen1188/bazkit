from django.db import models
from django.contrib.auth.models import AbstractUser


class User (AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username


class UserSettings(models.Model):
    SORTING_CHOICES = [
        ("category", "Nach Kategorie"),
        ("alphabetical", "Alphabetisch"),
        ("created", "Zuletzt hinzugefügt"),
    ]
    UNIT_CHOICES = [
        ("Stück", "Stück"),
        ("g", "Gramm"),
        ("kg", "Kilogramm"),
        ("ml", "Milliliter"),
        ("Liter", "Liter"),
        ("Packung", "Packung"),
    ]
    APPEARANCE_CHOICES = [
        ("light", "Hell"),
        ("dark", "Dunkel"),
        ("system", "System"),
    ]
    ACCENT_CHOICES = [
        ("green", "Grün"),
        ("blue", "Blau"),
        ("orange", "Orange"),
        ("red", "Rot"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    shopping_default_sorting = models.CharField(
        max_length=20,
        choices=SORTING_CHOICES,
        default="category",
    )
    shopping_default_unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="Stück",
    )
    shopping_move_completed_to_bottom = models.BooleanField(default=True)
    recipe_default_portions = models.PositiveSmallIntegerField(default=2)
    dietary_preferences = models.JSONField(default=list, blank=True)
    favorite_cuisines = models.JSONField(default=list, blank=True)
    appearance = models.CharField(
        max_length=10,
        choices=APPEARANCE_CHOICES,
        default="system",
    )
    accent_color = models.CharField(
        max_length=10,
        choices=ACCENT_CHOICES,
        default="green",
    )
    notification_shopping_reminders = models.BooleanField(default=True)
    notification_shared_lists = models.BooleanField(default=True)
    notification_product_updates = models.BooleanField(default=False)
    premium_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Einstellungen von {self.user.email}"


class AIRecipeUsage(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ai_recipe_usage",
    )
    period_start = models.DateField()
    generations_used = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KI-Nutzung von {self.user.email}: {self.generations_used}"
