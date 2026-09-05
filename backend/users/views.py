from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserLoginSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserSettingsSerializer,
)
from .models import UserSettings


class RegisterUserView(APIView):
    authentication_classes = []
    permission_classes = []

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

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=data["first_name"],
            last_name=data["last_name"],
            password=data["password"],
        )

        return Response(
            {
                "message":
                    "Registrierung erfolgreich.",

                "id": user.id,

                "first_name":
                    user.first_name,

                "last_name":
                    user.last_name,

                "email":
                    user.email,
            },
            status=status.HTTP_201_CREATED
        )


class LoginUserView(APIView):
    authentication_classes = []
    permission_classes = []

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

                "user": {
                    "id":
                        user.id,

                    "first_name":
                        user.first_name,

                    "last_name":
                        user.last_name,

                    "email":
                        user.email,
                }
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
        serializer.save()
        return Response(serializer.data)

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
