from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate


class UserRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Diese E-Mail wird bereits verwendet."
            )

        return value

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

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({
                "password2": "Die Passwörter stimmen nicht überein."
            })

        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "Diese E-Mail existiert nicht."
            })

        user = authenticate(
            username=email,
            password=password
        )

        if user is None:
            raise serializers.ValidationError({
                "password": "Das Passwort ist falsch."
            })

        attrs["user"] = user

        return attrs