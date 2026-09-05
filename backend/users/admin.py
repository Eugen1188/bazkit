from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AIRecipeUsage, User, UserSettings


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
        "premium_active",
        "appearance",
        "updated_at",
    )
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_filter = (
        "premium_active",
        "appearance",
        "accent_color",
        "shopping_default_sorting",
    )


@admin.register(AIRecipeUsage)
class AIRecipeUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "generations_used", "updated_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
