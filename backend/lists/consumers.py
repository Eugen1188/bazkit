from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core import signing
from django.db import models

from .models import SavedList


REALTIME_TICKET_SALT = "bazkit.saved-list.realtime"


@database_sync_to_async
def user_can_access_list(user_id, list_id):
    return SavedList.objects.filter(id=list_id).filter(
        models.Q(user_id=user_id) | models.Q(memberships__user_id=user_id),
        is_community_snapshot=False,
    ).exists()


class SavedListConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        query = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        ticket = (query.get("ticket") or [""])[0]
        try:
            payload = signing.loads(ticket, salt=REALTIME_TICKET_SALT, max_age=60)
            user_id = int(payload["user_id"])
        except (signing.BadSignature, KeyError, TypeError, ValueError):
            await self.close(code=4401)
            return

        self.list_id = int(self.scope["url_route"]["kwargs"]["list_id"])
        if not await user_can_access_list(user_id, self.list_id):
            await self.close(code=4403)
            return

        self.user_id = user_id
        self.group_name = f"saved_list_{self.list_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "list_id": self.list_id})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def saved_list_changed(self, event):
        if not await user_can_access_list(self.user_id, self.list_id):
            await self.close(code=4403)
            return
        await self.send_json(event["payload"])
