from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import User
from .storage import delete_avatar


@receiver(post_delete, sender=User)
def remove_deleted_user_avatar(sender, instance, **kwargs):
    delete_avatar(instance.avatar_key)
