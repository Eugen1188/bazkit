import uuid

import django.db.models.deletion
import lists.models
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def backfill_item_creators(apps, schema_editor):
    SavedListItem = apps.get_model("lists", "SavedListItem")
    items = SavedListItem.objects.filter(created_by__isnull=True).select_related("saved_list")
    for item in items.iterator(chunk_size=500):
        item.created_by_id = item.saved_list.user_id
        item.save(update_fields=["created_by"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lists", "0006_savedlist_is_community_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="savedlist",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="savedlistitem",
            name="checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="savedlistitem",
            name="checked_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="checked_saved_list_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="savedlistitem",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_saved_list_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="savedlistitem",
            name="is_checked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="savedlistitem",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(
            backfill_item_creators,
            migrations.RunPython.noop,
        ),
        migrations.CreateModel(
            name="SavedListMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("editor", "Kann bearbeiten"), ("viewer", "Kann ansehen")], default="editor", max_length=10)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("saved_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="lists.savedlist")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shared_saved_lists", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="SavedListInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("role", models.CharField(choices=[("editor", "Kann bearbeiten"), ("viewer", "Kann ansehen")], default="editor", max_length=10)),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(default=lists.models.saved_list_invitation_expiry)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("invited_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_saved_list_invitations", to=settings.AUTH_USER_MODEL)),
                ("saved_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="lists.savedlist")),
            ],
        ),
        migrations.AddConstraint(
            model_name="savedlistmembership",
            constraint=models.UniqueConstraint(fields=("saved_list", "user"), name="unique_saved_list_member"),
        ),
    ]
