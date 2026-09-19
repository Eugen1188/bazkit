import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from users.models import UserSettings

from .models import SavedList, SavedListNotificationDelivery
from .serializers import display_name


logger = logging.getLogger(__name__)
NOTIFICATION_COOLDOWN = timedelta(minutes=15)


def schedule_saved_list_notification(list_id, actor, action):
    if actor is None:
        return
    transaction.on_commit(
        lambda: notify_saved_list_members(list_id, actor.id, action)
    )


def notify_saved_list_members(list_id, actor_id, action):
    saved_list = (
        SavedList.objects.select_related("user")
        .prefetch_related("memberships__user")
        .filter(id=list_id, is_community_snapshot=False)
        .first()
    )
    if not saved_list or not saved_list.memberships.exists():
        return

    actor = saved_list.user if saved_list.user_id == actor_id else next(
        (membership.user for membership in saved_list.memberships.all() if membership.user_id == actor_id),
        None,
    )
    if actor is None:
        return

    action_text = {
        "list.updated": "hat die Liste bearbeitet",
        "item.updated": "hat ein Produkt bearbeitet",
        "item.deleted": "hat ein Produkt entfernt",
        "item.checked": "hat den Einkaufsstand geändert",
    }.get(action, "hat die Liste geändert")
    recipients = [saved_list.user, *(membership.user for membership in saved_list.memberships.all())]
    now = timezone.now()

    for recipient in recipients:
        if recipient.id == actor_id or not recipient.email:
            continue
        preference = UserSettings.objects.filter(user=recipient).values_list(
            "notification_shared_lists", flat=True
        ).first()
        if preference is False:
            continue

        delivery, _created = SavedListNotificationDelivery.objects.get_or_create(
            saved_list=saved_list,
            user=recipient,
        )
        if delivery.last_sent_at and delivery.last_sent_at > now - NOTIFICATION_COOLDOWN:
            continue

        list_url = f"{settings.FRONTEND_URL.rstrip('/')}/main/saved-list/{saved_list.id}"
        try:
            send_mail(
                f"Änderung an „{saved_list.title}“",
                (
                    f"{display_name(actor)} {action_text}.\n\n"
                    f"Liste öffnen: {list_url}\n\n"
                    "Diese Benachrichtigungen kannst du in den Einstellungen ausschalten."
                ),
                None,
                [recipient.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception(
                "Saved-list change notification could not be sent",
                extra={"monitoring_source": "email"},
            )
            continue

        delivery.last_sent_at = now
        delivery.save(update_fields=["last_sent_at"])
