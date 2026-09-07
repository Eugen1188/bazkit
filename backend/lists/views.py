import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import status

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)

from rest_framework.response import Response

from rest_framework.views import APIView


from recipes.models import Recipe
from products.pricing import scaled_price


from .models import (
    SavedList,
    SavedListInvitation,
    SavedListItem,
    SavedListMembership,
    ShoppingList,
    ShoppingListItem
)


from .serializers import (
    SavedListSerializer,
    SavedListSummarySerializer,
    SavedListDetailSerializer,
    SavedListItemSerializer,
    SavedListInvitationSerializer,
    ShoppingListSerializer,
    ShoppingListItemSerializer
)
from .serializers import access_role, display_name
from users.storage import get_avatar_url


logger = logging.getLogger(__name__)
User = get_user_model()


PRICE_SNAPSHOT_FIELDS = (
    "estimated_price", "price_source", "price_currency", "price_date",
    "price_store", "price_sample_count", "price_min", "price_max",
    "package_price", "package_quantity", "package_unit",
)


# ==========================================
# SAVED LISTS
# ==========================================


def accessible_saved_lists(user):
    return (
        SavedList.objects
        .filter(
            Q(user=user) | Q(memberships__user=user),
            is_community_snapshot=False,
        )
        .distinct()
    )


def can_edit_saved_list(saved_list, user):
    return access_role(saved_list, user) in {"owner", "editor"}


def touch_saved_list(saved_list_id):
    SavedList.objects.filter(pk=saved_list_id).update(updated_at=timezone.now())


def saved_list_queryset(user):
    return (
        accessible_saved_lists(user)
        .select_related("user")
        .prefetch_related(
            "memberships__user",
            "items__product",
            "items__created_by",
            "items__checked_by",
        )
    )


class SavedListListCreateAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        saved_lists = (
            accessible_saved_lists(request.user)
            .select_related("user")
            .prefetch_related("memberships__user")
            .annotate(
                item_count=Count("items", distinct=True),
                checked_count=Count(
                    "items",
                    filter=Q(items__is_checked=True),
                    distinct=True,
                ),
            )
            .order_by(
                "-updated_at"
            )
        )

        serializer = SavedListSummarySerializer(
            saved_lists,
            many=True,
            context={"request": request},
        )

        return Response(
            serializer.data
        )


    def post(
        self,
        request
    ):
        serializer = SavedListSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        saved_list = serializer.save()

        return Response(
            SavedListSerializer(
                saved_list,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED
        )


class SavedListDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        pk
    ):
        return saved_list_queryset(request.user).filter(id=pk).first()


    def get(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = (
            SavedListDetailSerializer(
                saved_list,
                context={"request": request},
            )
        )

        return Response(
            serializer.data
        )


    def put(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not can_edit_saved_list(saved_list, request.user):
            return Response(
                {"detail": "Du darfst diese Liste nur ansehen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SavedListSerializer(
            saved_list,
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_list = (
            serializer.save()
        )

        updated_list = saved_list_queryset(request.user).get(pk=updated_list.pk)

        return Response(
            SavedListSerializer(
                updated_list,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK
        )


    def delete(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if saved_list.user_id != request.user.id:
            return Response(
                {"detail": "Nur der Eigentümer kann die Liste löschen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        saved_list.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SavedListItemDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        list_id,
        item_id
    ):
        saved_list = saved_list_queryset(request.user).filter(id=list_id).first()
        if not saved_list:
            return None
        return (
            SavedListItem.objects
            .select_related("saved_list", "product", "created_by", "checked_by")
            .filter(id=item_id, saved_list=saved_list)
            .first()
        )


    def put(
        self,
        request,
        list_id,
        item_id
    ):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not can_edit_saved_list(item.saved_list, request.user):
            return Response(
                {"detail": "Du darfst diese Liste nur ansehen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = (
            SavedListItemSerializer(
                item,
                data=request.data,
                partial=True
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        touch_saved_list(list_id)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    def delete(
        self,
        request,
        list_id,
        item_id
    ):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not can_edit_saved_list(item.saved_list, request.user):
            return Response(
                {"detail": "Du darfst diese Liste nur ansehen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        item.delete()

        touch_saved_list(list_id)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SavedListItemToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, list_id, item_id):
        saved_list = saved_list_queryset(request.user).filter(id=list_id).first()
        if not saved_list:
            return Response(
                {"detail": "Liste nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not can_edit_saved_list(saved_list, request.user):
            return Response(
                {"detail": "Du darfst diese Liste nur ansehen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        item = (
            SavedListItem.objects.select_for_update()
            .select_related("product", "created_by", "checked_by")
            .filter(id=item_id, saved_list=saved_list)
            .first()
        )
        if not item:
            return Response(
                {"detail": "Produkt nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        requested_state = request.data.get("is_checked", not item.is_checked)
        if not isinstance(requested_state, bool):
            return Response(
                {"is_checked": ["Der Wert muss wahr oder falsch sein."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.is_checked = requested_state
        item.checked_by = request.user if requested_state else None
        item.checked_at = timezone.now() if requested_state else None
        item.save(update_fields=["is_checked", "checked_by", "checked_at", "updated_at"])
        touch_saved_list(saved_list.id)
        return Response(SavedListItemSerializer(item).data)


def collaboration_member(
    user,
    role,
    membership_id=None,
    joined_at=None,
    is_owner=False,
    include_email=True,
):
    return {
        "id": membership_id,
        "user_id": user.id,
        "display_name": display_name(user),
        "email": user.email if include_email else "",
        "avatar_url": get_avatar_url(user.avatar_key),
        "role": role,
        "is_owner": is_owner,
        "joined_at": joined_at,
    }


class SavedListCollaborationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_list(self, request, list_id):
        return saved_list_queryset(request.user).filter(id=list_id).first()

    def get(self, request, list_id):
        saved_list = self.get_list(request, list_id)
        if not saved_list:
            return Response(
                {"detail": "Liste nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        members = [
            collaboration_member(
                saved_list.user,
                "owner",
                joined_at=saved_list.created_at,
                is_owner=True,
                include_email=saved_list.user_id == request.user.id,
            )
        ]
        members.extend(
            collaboration_member(
                membership.user,
                membership.role,
                membership_id=membership.id,
                joined_at=membership.joined_at,
                include_email=saved_list.user_id == request.user.id,
            )
            for membership in saved_list.memberships.all()
        )

        invitations = []
        if saved_list.user_id == request.user.id:
            pending = saved_list.invitations.filter(
                accepted_at__isnull=True,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).order_by("-created_at")
            invitations = SavedListInvitationSerializer(
                pending,
                many=True,
                context={"frontend_url": settings.FRONTEND_URL},
            ).data

        return Response({
            "members": members,
            "invitations": invitations,
            "can_manage": saved_list.user_id == request.user.id,
        })

    def post(self, request, list_id):
        saved_list = self.get_list(request, list_id)
        if not saved_list:
            return Response(
                {"detail": "Liste nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if saved_list.user_id != request.user.id:
            return Response(
                {"detail": "Nur der Eigentümer kann Personen einladen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        recently_created = SavedListInvitation.objects.filter(
            invited_by=request.user,
            created_at__gte=timezone.now() - timedelta(minutes=10),
        ).count()
        if recently_created >= 10:
            return Response(
                {"detail": "Du hast gerade viele Einladungen erstellt. Bitte warte einige Minuten."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        email = str(request.data.get("email", "")).strip().lower()
        role = str(request.data.get("role", SavedListMembership.EDITOR)).strip()
        if role not in {SavedListMembership.EDITOR, SavedListMembership.VIEWER}:
            return Response(
                {"role": ["Bitte wähle eine gültige Berechtigung."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email:
            try:
                validate_email(email)
            except ValidationError:
                return Response(
                    {"email": ["Bitte gib eine gültige E-Mail-Adresse ein."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if email.casefold() == request.user.email.casefold():
                return Response(
                    {"email": ["Du bist bereits Eigentümer dieser Liste."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            invited_user = User.objects.filter(email__iexact=email).first()
            if invited_user and saved_list.memberships.filter(user=invited_user).exists():
                return Response(
                    {"email": ["Diese Person arbeitet bereits an der Liste mit."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            saved_list.invitations.filter(
                email__iexact=email,
                accepted_at__isnull=True,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())

        active_invitation_count = saved_list.invitations.filter(
            accepted_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).count()
        if saved_list.memberships.count() + active_invitation_count >= 25:
            return Response(
                {"detail": "Eine Liste kann mit höchstens 25 weiteren Personen geteilt werden."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = SavedListInvitation.objects.create(
            saved_list=saved_list,
            invited_by=request.user,
            email=email,
            role=role,
        )
        invite_url = f"{settings.FRONTEND_URL.rstrip('/')}/invite/{invitation.token}"
        email_sent = False
        if email:
            try:
                permission = "bearbeiten und Produkte abhaken" if role == "editor" else "ansehen"
                send_mail(
                    f"Einladung zur bazkit-Liste „{saved_list.title}“",
                    (
                        f"{display_name(request.user)} hat dich zur Einkaufsliste „{saved_list.title}“ eingeladen.\n\n"
                        f"Du darfst die Liste {permission}.\n\n"
                        f"Einladung annehmen: {invite_url}\n\n"
                        "Der Link ist sieben Tage gültig."
                    ),
                    None,
                    [email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception:
                logger.exception("Saved list invitation email could not be sent")

        payload = SavedListInvitationSerializer(
            invitation,
            context={"frontend_url": settings.FRONTEND_URL},
        ).data
        payload["email_sent"] = email_sent
        touch_saved_list(saved_list.id)
        return Response(payload, status=status.HTTP_201_CREATED)


class SavedListInvitationManageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_invitation(self, request, list_id, invitation_id):
        return SavedListInvitation.objects.filter(
            id=invitation_id,
            saved_list_id=list_id,
            saved_list__user=request.user,
        ).first()

    def patch(self, request, list_id, invitation_id):
        invitation = self.get_invitation(request, list_id, invitation_id)
        if not invitation:
            return Response({"detail": "Einladung nicht gefunden."}, status=404)
        if invitation.status != "pending":
            return Response({"detail": "Diese Einladung ist nicht mehr aktiv."}, status=409)
        role = str(request.data.get("role", ""))
        if role not in {SavedListMembership.EDITOR, SavedListMembership.VIEWER}:
            return Response({"role": ["Ungültige Berechtigung."]}, status=400)
        invitation.role = role
        invitation.save(update_fields=["role"])
        return Response(SavedListInvitationSerializer(
            invitation,
            context={"frontend_url": settings.FRONTEND_URL},
        ).data)

    def delete(self, request, list_id, invitation_id):
        invitation = self.get_invitation(request, list_id, invitation_id)
        if not invitation:
            return Response({"detail": "Einladung nicht gefunden."}, status=404)
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at"])
        touch_saved_list(list_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedListMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_membership(self, request, list_id, membership_id):
        return SavedListMembership.objects.select_related("saved_list", "user").filter(
            id=membership_id,
            saved_list_id=list_id,
            saved_list__user=request.user,
        ).first()

    def patch(self, request, list_id, membership_id):
        membership = self.get_membership(request, list_id, membership_id)
        if not membership:
            return Response({"detail": "Mitglied nicht gefunden."}, status=404)
        role = str(request.data.get("role", ""))
        if role not in {SavedListMembership.EDITOR, SavedListMembership.VIEWER}:
            return Response({"role": ["Ungültige Berechtigung."]}, status=400)
        membership.role = role
        membership.save(update_fields=["role"])
        touch_saved_list(list_id)
        return Response(collaboration_member(
            membership.user,
            membership.role,
            membership_id=membership.id,
            joined_at=membership.joined_at,
        ))

    def delete(self, request, list_id, membership_id):
        membership = self.get_membership(request, list_id, membership_id)
        if not membership:
            return Response({"detail": "Mitglied nicht gefunden."}, status=404)
        membership.delete()
        touch_saved_list(list_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedListLeaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, list_id):
        membership = SavedListMembership.objects.filter(
            saved_list_id=list_id,
            user=request.user,
        ).first()
        if not membership:
            return Response(
                {"detail": "Du bist kein Mitglied dieser Liste."},
                status=status.HTTP_404_NOT_FOUND,
            )
        membership.delete()
        touch_saved_list(list_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


def masked_email(email):
    if not email or "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    visible = local[:2]
    return f"{visible}{'*' * max(2, len(local) - len(visible))}@{domain}"


class SavedListInvitationAPIView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "POST" else [AllowAny()]

    def get_invitation(self, token):
        return (
            SavedListInvitation.objects
            .select_related("saved_list", "invited_by")
            .filter(token=token)
            .first()
        )

    def get(self, request, token):
        invitation = self.get_invitation(token)
        if not invitation:
            return Response({"detail": "Einladung nicht gefunden.", "status": "invalid"}, status=404)
        can_open = False
        if getattr(request.user, "is_authenticated", False):
            can_open = accessible_saved_lists(request.user).filter(
                id=invitation.saved_list_id,
            ).exists()
        return Response({
            "status": invitation.status,
            "list_id": invitation.saved_list_id,
            "list_title": invitation.saved_list.title,
            "inviter_name": display_name(invitation.invited_by),
            "role": invitation.role,
            "expires_at": invitation.expires_at,
            "email_required": bool(invitation.email),
            "invited_email": masked_email(invitation.email),
            "can_open": can_open,
        })

    @transaction.atomic
    def post(self, request, token):
        invitation = (
            SavedListInvitation.objects.select_for_update()
            .select_related("saved_list", "invited_by")
            .filter(token=token)
            .first()
        )
        if not invitation:
            return Response({"detail": "Einladung nicht gefunden."}, status=404)
        if invitation.status != "pending":
            return Response(
                {"detail": "Diese Einladung ist abgelaufen oder nicht mehr gültig."},
                status=status.HTTP_409_CONFLICT,
            )
        if invitation.email and invitation.email.casefold() != request.user.email.casefold():
            return Response(
                {"detail": "Diese Einladung wurde an eine andere E-Mail-Adresse gesendet."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if invitation.saved_list.user_id == request.user.id:
            return Response(
                {"detail": "Du bist bereits Eigentümer dieser Liste."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_membership = SavedListMembership.objects.filter(
            saved_list=invitation.saved_list,
            user=request.user,
        ).first()
        if existing_membership is None and invitation.saved_list.memberships.count() >= 25:
            return Response(
                {"detail": "Diese Liste hat bereits die maximale Anzahl an Mitgliedern."},
                status=status.HTTP_409_CONFLICT,
            )

        membership, created = SavedListMembership.objects.get_or_create(
            saved_list=invitation.saved_list,
            user=request.user,
            defaults={"role": invitation.role},
        )
        if not created and membership.role != invitation.role:
            membership.role = invitation.role
            membership.save(update_fields=["role"])
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        touch_saved_list(invitation.saved_list_id)
        return Response({
            "message": "Du arbeitest jetzt an dieser Liste mit.",
            "list_id": invitation.saved_list_id,
            "role": membership.role,
        })


# ==========================================
# SHOPPING LIST
# ==========================================


class ShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_shopping_list(
        self,
        request
    ):
        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        return shopping_list


    def get(
        self,
        request
    ):
        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items__product"
            )
            .filter(
                user=request.user
            )
            .first()
        )

        if shopping_list is None:
            shopping_list = ShoppingList.objects.create(user=request.user)

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data
        )


    def delete(
        self,
        request
    ):
        shopping_list = (
            self.get_shopping_list(
                request
            )
        )

        shopping_list.items.all().delete()

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )


class ShoppingListItemCreateAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def post(
        self,
        request
    ):
        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        serializer = (
            ShoppingListItemSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        item = serializer.save(
            shopping_list=
                shopping_list
        )

        return Response(
            ShoppingListItemSerializer(
                item
            ).data,
            status=status.HTTP_201_CREATED
        )


class ShoppingListItemDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        item_id
    ):
        return (
            ShoppingListItem.objects
            .filter(
                id=item_id,
                shopping_list__user=
                    request.user
            )
            .first()
        )


    def patch(
        self,
        request,
        item_id
    ):
        item = self.get_object(
            request,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = (
            ShoppingListItemSerializer(
                item,
                data=request.data,
                partial=True
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data
        )


    def delete(
        self,
        request,
        item_id
    ):
        item = self.get_object(
            request,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class AddSavedListToShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    @transaction.atomic
    def post(
        self,
        request,
        saved_list_id
    ):
        saved_list = (
            accessible_saved_lists(request.user)
            .filter(id=saved_list_id)
            .prefetch_related(
                "items"
            )
            .first()
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Gespeicherte Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        new_items = []

        for saved_item in (
            saved_list.items.all()
        ):
            new_items.append(
                ShoppingListItem(
                    shopping_list=
                        shopping_list,

                    product=
                        saved_item.product,

                    name=
                        (
                            saved_item.name
                            or
                            (
                                saved_item
                                .product.name
                                if
                                saved_item.product
                                else ""
                            )
                        ),

                    quantity=
                        saved_item.quantity,

                    unit=
                        saved_item.unit,

                    note=
                        saved_item.note,

                    is_checked=False,

                    **{
                        field: getattr(saved_item, field)
                        for field in PRICE_SNAPSHOT_FIELDS
                    }
                )
            )

        ShoppingListItem.objects.bulk_create(
            new_items
        )

        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items"
            )
            .get(
                id=shopping_list.id
            )
        )

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )


class AddRecipeToShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    @transaction.atomic
    def post(
        self,
        request,
        recipe_id
    ):
        recipe = (
            Recipe.objects
            .filter(
                id=recipe_id,
                user=request.user
            )
            .prefetch_related(
                "ingredients__product"
            )
            .first()
        )


        if not recipe:
            return Response(
                {
                    "detail":
                        "Rezept nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )


        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )


        new_items = []

        included_pantry_ids = request.data.get("included_pantry_product_ids")
        if included_pantry_ids is not None:
            if not isinstance(included_pantry_ids, list):
                return Response(
                    {"detail": "Die ausgewählten Vorratszutaten sind ungültig."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                included_pantry_ids = {int(value) for value in included_pantry_ids}
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Die ausgewählten Vorratszutaten sind ungültig."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


        for ingredient in (
            recipe.ingredients.all()
        ):

            if (
                included_pantry_ids is not None
                and ingredient.product is not None
                and ingredient.product.is_common_pantry
                and ingredient.product_id not in included_pantry_ids
            ):
                continue

            price_data = {
                field: getattr(ingredient, field)
                for field in PRICE_SNAPSHOT_FIELDS
            }

            if ingredient.package_price is not None:
                price_data["estimated_price"] = scaled_price(
                    ingredient.package_price,
                    ingredient.package_quantity,
                    ingredient.package_unit,
                    ingredient.quantity,
                    ingredient.unit,
                    mode="purchase",
                )
                price_data["price_min"] = None
                price_data["price_max"] = None

            new_items.append(
                ShoppingListItem(
                    shopping_list=
                        shopping_list,

                    product=
                        ingredient.product,

                    name=
                        ingredient.name,

                    quantity=
                        ingredient.quantity,

                    unit=
                        ingredient.unit,

                    note='',

                    is_checked=False,

                    **price_data
                )
            )


        ShoppingListItem.objects.bulk_create(
            new_items
        )


        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items"
            )
            .get(
                id=shopping_list.id
            )
        )


        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )
