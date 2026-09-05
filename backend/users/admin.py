from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserSettings


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "id",
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "created_at",
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "shopping_default_sorting",
        "recipe_default_portions",
        "appearance",
        "updated_at",
    )
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_filter = ("appearance", "accent_color", "shopping_default_sorting")
