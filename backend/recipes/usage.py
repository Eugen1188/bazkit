from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from users.models import AIRecipeUsage, UserSettings


class AIRecipeQuotaExceeded(Exception):
    def __init__(self, usage):
        self.usage = usage
        super().__init__("Das monatliche KI-Kontingent ist aufgebraucht.")


def _current_period_start():
    today = timezone.localdate()
    return today.replace(day=1)


def _next_period_start(period_start):
    if period_start.month == 12:
        return date(period_start.year + 1, 1, 1)
    return date(period_start.year, period_start.month + 1, 1)


def _plan_for(user):
    user_settings, _created = UserSettings.objects.get_or_create(user=user)
    enforcement_enabled = settings.PREMIUM_ENFORCEMENT_ENABLED
    is_premium = not enforcement_enabled or user_settings.premium_active
    if is_premium:
        return {
            "plan": "premium",
            "plan_label": (
                "Premium" if enforcement_enabled else "Premium-Startphase"
            ),
            "limit": max(0, settings.AI_RECIPE_PREMIUM_MONTHLY_LIMIT),
            "is_premium": True,
            "premium_enforcement_enabled": enforcement_enabled,
        }
    return {
        "plan": "free",
        "plan_label": "Basis",
        "limit": max(0, settings.AI_RECIPE_FREE_MONTHLY_LIMIT),
        "is_premium": False,
        "premium_enforcement_enabled": enforcement_enabled,
    }


def _status(user, usage):
    plan = _plan_for(user)
    used = usage.generations_used
    limit = plan["limit"]
    return {
        **plan,
        "used": used,
        "remaining": max(0, limit - used),
        "period_start": usage.period_start.isoformat(),
        "resets_at": _next_period_start(usage.period_start).isoformat(),
    }


def _locked_usage(user):
    period_start = _current_period_start()
    usage, _created = AIRecipeUsage.objects.select_for_update().get_or_create(
        user=user,
        defaults={"period_start": period_start},
    )
    if usage.period_start != period_start:
        usage.period_start = period_start
        usage.generations_used = 0
        usage.save(update_fields=["period_start", "generations_used", "updated_at"])
    return usage


def get_ai_recipe_usage(user):
    with transaction.atomic():
        return _status(user, _locked_usage(user))


def reserve_ai_recipe_generation(user):
    with transaction.atomic():
        usage = _locked_usage(user)
        status = _status(user, usage)
        if status["remaining"] <= 0:
            raise AIRecipeQuotaExceeded(status)
        usage.generations_used += 1
        usage.save(update_fields=["generations_used", "updated_at"])
        return _status(user, usage)


def refund_ai_recipe_generation(user):
    with transaction.atomic():
        usage = _locked_usage(user)
        if usage.generations_used > 0:
            usage.generations_used -= 1
            usage.save(update_fields=["generations_used", "updated_at"])
        return _status(user, usage)
