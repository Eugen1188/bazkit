import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


logger = logging.getLogger(__name__)


def broadcast_saved_list_change(list_id, *, action="updated", actor=None):
    payload = {
        "type": "saved-list.changed",
        "list_id": list_id,
        "action": action,
        "actor_id": getattr(actor, "id", None),
        "actor_name": (
            actor.get_full_name().strip() or actor.email or actor.username
            if actor is not None
            else ""
        ),
    }

    def send():
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            async_to_sync(channel_layer.group_send)(
                f"saved_list_{list_id}",
                {"type": "saved_list_changed", "payload": payload},
            )
        except Exception:
            logger.exception("Saved-list realtime event could not be delivered")

    transaction.on_commit(send)
