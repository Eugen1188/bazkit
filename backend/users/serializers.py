import re

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=150
    )

    last_name = serializers.CharField(
        max_length=150
    )

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password2 = serializers.CharField(
        write_only=True
    )

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise serializers.ValidationError(
                "Diese E-Mail wird bereits verwendet."
            )

        return email

    def validate_first_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Bitte geben Sie einen Vornamen ein."
            )

        return value

    def validate_last_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Bitte geben Sie einen Nachnamen ein."
            )

        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Das Passwort muss mindestens 8 Zeichen lang sein."
            )

        if not re.search(
            r"[A-Za-zÄÖÜäöüß]",
            value
        ):
            raise serializers.ValidationError(
                "Das Passwort muss mindestens einen Buchstaben enthalten."
            )

        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Das Passwort muss mindestens eine Zahl enthalten."
            )

        return value

    def validate(self, attrs):
        if (
            attrs["password"] !=
            attrs["password2"]
        ):
            raise serializers.ValidationError({
                "password2":
                    "Die Passwörter stimmen nicht überein."
            })

        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        entered_email = (
            attrs.get("email", "")
            .strip()
            .lower()
        )

        password = attrs.get("password")

        try:
            user = User.objects.get(
                email__iexact=entered_email
            )

        except User.DoesNotExist:
            raise serializers.ValidationError(
                "E-Mail oder Passwort ist falsch."
            )

        user = authenticate(
            username=user.username,
            password=password
        )

        if user is None:
            raise serializers.ValidationError(
                "E-Mail oder Passwort ist falsch."
            )

        attrs["user"] = user

        return attrs