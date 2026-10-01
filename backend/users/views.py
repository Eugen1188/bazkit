import logging
from binascii import Error as BinasciiError
from datetime import timedelta
from uuid import UUID, uuid4

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenRefreshView

from .email_verification import send_password_reset_email, send_verification_email
from .models import User
from .serializers import (
    UserLoginSerializer,
    ContactSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserSettingsSerializer,
)
from .models import UserSettings
from .throttles import (
    ContactThrottle,
    LoginThrottle,
    PasswordResetConfirmThrottle,
    PasswordResetRequestThrottle,
    RegistrationThrottle,
    RefreshTokenThrottle,
    VerificationResendThrottle,
    VerificationThrottle,
)
from .storage import AvatarImageError, delete_avatar, upload_avatar


logger = logging.getLogger(__name__)


class PublicThrottleMixin:
    def get_throttles(self):
        if not getattr(settings, "AUTH_THROTTLES_ENABLED", True):
            return []
        return super().get_throttles()


class PasswordBoundTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(jwt_settings.USER_ID_CLAIM)
        password_hash = refresh.payload.get(jwt_settings.REVOKE_TOKEN_CLAIM)
        user = User.objects.filter(
            **{jwt_settings.USER_ID_FIELD: user_id},
            is_active=True,
        ).first()
        if (
            user is None
            or not password_hash
            or password_hash != get_md5_hash_password(user.password)
        ):
            raise AuthenticationFailed(
                "Die Sitzung ist nicht mehr gültig. Bitte melde dich erneut an.",
                code="password_changed",
            )
        return super().validate(attrs)


class ThrottledTokenRefreshView(PublicThrottleMixin, TokenRefreshView):
    throttle_classes = [RefreshTokenThrottle]
    serializer_class = PasswordBoundTokenRefreshSerializer


class RegisterUserView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [RegistrationThrottle]

    def post(self, request):
        serializer = UserRegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        email = (
            data["email"]
            .strip()
            .lower()
        )

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    password=data["password"],
                    is_active=False,
                    email_verification_token=uuid4(),
                    email_verification_sent_at=timezone.now(),
                    terms_accepted_at=timezone.now(),
                    terms_version=settings.LEGAL_TERMS_VERSION,
                )
                send_verification_email(user, email)
        except Exception:
            logger.exception(
                "Registration verification email could not be sent",
                extra={"monitoring_source": "email"},
            )
            return Response(
                {
                    "detail": (
                        "Die Bestätigungs-E-Mail konnte nicht versendet werden. "
                        "Bitte versuche es später erneut."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message":
                    "Prüfe dein E-Mail-Postfach und bestätige dein Konto.",

                "id": user.id,

                "first_name":
                    user.first_name,

                "last_name":
                    user.last_name,

                "email": user.email,
                "verification_required": True,
            },
            status=status.HTTP_201_CREATED
        )


class LoginUserView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data[
            "user"
        ]

        refresh = RefreshToken.for_user(
            user
        )

        return Response(
            {
                "refresh":
                    str(refresh),

                "access":
                    str(refresh.access_token),

                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        requested_email = serializer.validated_data.get(
            "email",
            request.user.email,
        ).strip().lower()
        email_changed = requested_email.casefold() != request.user.email.casefold()

        try:
            with transaction.atomic():
                serializer.save()
                if email_changed:
                    request.user.pending_email = requested_email
                    request.user.email_verification_token = uuid4()
                    request.user.email_verification_sent_at = timezone.now()
                    request.user.save(update_fields=[
                        "pending_email",
                        "email_verification_token",
                        "email_verification_sent_at",
                    ])
                    send_verification_email(
                        request.user,
                        requested_email,
                        email_change=True,
                    )
        except Exception:
            logger.exception(
                "Email change verification could not be sent",
                extra={"monitoring_source": "email"},
            )
            return Response(
                {
                    "detail": (
                        "Die Bestätigungs-E-Mail konnte nicht versendet werden. "
                        "Deine Änderungen wurden nicht gespeichert."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = UserProfileSerializer(request.user).data
        response_data["email_change_pending"] = email_changed
        response_data["message"] = (
            f"Wir haben einen Bestätigungslink an {requested_email} gesendet."
            if email_changed
            else "Dein Profil wurde aktualisiert."
        )
        return Response(response_data)

    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_settings(user):
        settings, _created = UserSettings.objects.get_or_create(user=user)
        return settings

    def get(self, request):
        settings = self.get_settings(request.user)
        return Response(UserSettingsSerializer(settings).data)

    def patch(self, request):
        settings = self.get_settings(request.user)
        serializer = UserSettingsSerializer(
            settings,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"message": "Passwort wurde geändert."})


class VerifyEmailView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [VerificationThrottle]

    @transaction.atomic
    def post(self, request):
        try:
            token = UUID(str(request.data.get("token", "")))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Der Bestätigungslink ist ungültig."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = (
            User.objects.select_for_update()
            .filter(email_verification_token=token)
            .first()
        )
        if user is None or user.email_verification_sent_at is None:
            return Response(
                {"detail": "Der Bestätigungslink ist ungültig oder wurde bereits verwendet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = user.email_verification_sent_at + timedelta(
            hours=settings.EMAIL_VERIFICATION_TIMEOUT_HOURS
        )
        if timezone.now() > expires_at:
            return Response(
                {
                    "detail": "Der Bestätigungslink ist abgelaufen. Fordere einen neuen Link an.",
                    "code": "verification_link_expired",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_changed = bool(user.pending_email)
        if email_changed:
            address_is_used = User.objects.filter(
                email__iexact=user.pending_email
            ).exclude(pk=user.pk).exists()
            username_is_used = User.objects.filter(
                username__iexact=user.pending_email
            ).exclude(pk=user.pk).exists()
            if address_is_used or username_is_used:
                return Response(
                    {"detail": "Diese E-Mail-Adresse wird inzwischen bereits verwendet."},
                    status=status.HTTP_409_CONFLICT,
                )
            user.email = user.pending_email
            user.username = user.pending_email
            user.pending_email = ""

        user.is_active = True
        user.email_verified_at = timezone.now()
        user.email_verification_token = None
        user.email_verification_sent_at = None
        user.save(update_fields=[
            "email",
            "username",
            "pending_email",
            "is_active",
            "email_verified_at",
            "email_verification_token",
            "email_verification_sent_at",
        ])
        return Response({
            "message": (
                "Deine neue E-Mail-Adresse wurde bestätigt."
                if email_changed
                else "Dein Konto wurde erfolgreich freigeschaltet."
            ),
            "email": user.email,
        })


class ResendVerificationEmailView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [VerificationResendThrottle]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        generic_message = (
            "Falls für diese Adresse eine Bestätigung aussteht, wurde ein neuer Link versendet."
        )
        if not email:
            return Response({"detail": "Bitte gib deine E-Mail-Adresse ein."}, status=400)

        user = User.objects.filter(email__iexact=email, is_active=False).first()
        email_change = False
        if user is None:
            user = User.objects.filter(pending_email__iexact=email).first()
            email_change = user is not None
        if user is None:
            return Response({"message": generic_message})

        cooldown = timedelta(seconds=settings.EMAIL_VERIFICATION_RESEND_SECONDS)
        if (
            user.email_verification_sent_at
            and timezone.now() - user.email_verification_sent_at < cooldown
        ):
            return Response({"message": generic_message})

        try:
            with transaction.atomic():
                user.email_verification_token = uuid4()
                user.email_verification_sent_at = timezone.now()
                user.save(update_fields=[
                    "email_verification_token",
                    "email_verification_sent_at",
                ])
                send_verification_email(user, email, email_change=email_change)
        except Exception:
            logger.exception(
                "Verification email could not be resent",
                extra={"monitoring_source": "email"},
            )
            return Response(
                {"detail": "Die E-Mail konnte momentan nicht versendet werden."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"message": generic_message})


class PasswordResetRequestView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        generic_message = (
            "Falls ein aktives Konto zu dieser Adresse gehört, wurde ein Link versendet."
        )
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            is_active=True,
        ).first()
        if user is None:
            return Response({"message": generic_message})
        try:
            send_password_reset_email(user)
        except Exception:
            logger.exception(
                "Password reset email could not be sent",
                extra={"monitoring_source": "email"},
            )
        return Response({"message": generic_message})


class PasswordResetConfirmView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [PasswordResetConfirmThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, BinasciiError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(
            user,
            serializer.validated_data["token"],
        ):
            return Response(
                {"detail": "Der Link ist ungültig oder abgelaufen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "Dein Passwort wurde erfolgreich geändert."})


class ContactView(PublicThrottleMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ContactThrottle]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        body = (
            f"Name: {data['name']}\n"
            f"E-Mail: {data['email']}\n\n"
            f"{data['message']}"
        )
        try:
            message = EmailMessage(
                subject=f"[Bazkit Kontakt] {data['subject']}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[data["email"]],
            )
            message.send(fail_silently=False)
        except Exception:
            logger.exception(
                "Contact email could not be sent",
                extra={"monitoring_source": "email"},
            )
            return Response(
                {"detail": "Deine Nachricht konnte momentan nicht versendet werden."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"message": "Danke! Deine Nachricht wurde versendet."})


class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        uploaded_file = request.FILES.get("avatar")
        if uploaded_file is None:
            return Response(
                {"avatar": ["Bitte wähle ein Bild aus."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_key = request.user.avatar_key
        try:
            new_key = upload_avatar(uploaded_file, request.user.id)
        except AvatarImageError as error:
            return Response(
                {"avatar": [str(error)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.avatar_key = new_key
        request.user.save(update_fields=["avatar_key"])
        if old_key and old_key != new_key:
            delete_avatar(old_key)
        return Response(UserProfileSerializer(request.user).data)

    def delete(self, request):
        old_key = request.user.avatar_key
        if old_key:
            request.user.avatar_key = ""
            request.user.save(update_fields=["avatar_key"])
            delete_avatar(old_key)
        return Response(UserProfileSerializer(request.user).data)
