import re

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User
from .models import UserSettings


DIETARY_PREFERENCES = {
    "vegetarian",
    "vegan",
    "gluten_free",
    "lactose_free",
    "low_carb",
    "high_protein",
}

FAVORITE_CUISINES = {
    "italian",
    "asian",
    "german",
    "mexican",
    "greek",
    "mediterranean",
    "indian",
}


def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError(
            "Das Passwort muss mindestens 8 Zeichen lang sein."
        )

    if not re.search(r"[A-Za-zÄÖÜäöüß]", value):
        raise serializers.ValidationError(
            "Das Passwort muss mindestens einen Buchstaben enthalten."
        )

    if not re.search(r"\d", value):
        raise serializers.ValidationError(
            "Das Passwort muss mindestens eine Zahl enthalten."
        )

    return value


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

    accept_terms = serializers.BooleanField(
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
        return validate_password_strength(value)

    def validate_accept_terms(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Bitte akzeptiere die Nutzungsbedingungen."
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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined")

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Bitte gib einen Vornamen ein.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Bitte gib einen Nachnamen ein.")
        return value

    def validate_email(self, value):
        email = value.strip().lower()
        existing = User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        )
        if existing.exists():
            raise serializers.ValidationError(
                "Diese E-Mail-Adresse wird bereits verwendet."
            )
        return email

    def update(self, instance, validated_data):
        email = validated_data.get("email")
        if email:
            validated_data["username"] = email
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Das aktuelle Passwort ist falsch.")
        return value

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({
                "new_password2": "Die neuen Passwörter stimmen nicht überein."
            })
        return attrs


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = (
            "shopping_default_sorting",
            "shopping_default_unit",
            "shopping_move_completed_to_bottom",
            "recipe_default_portions",
            "dietary_preferences",
            "favorite_cuisines",
            "appearance",
            "accent_color",
            "notification_shopping_reminders",
            "notification_shared_lists",
            "notification_product_updates",
            "premium_active",
            "updated_at",
        )
        read_only_fields = ("premium_active", "updated_at")

    def validate_recipe_default_portions(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError(
                "Die Standard-Portionsgröße muss zwischen 1 und 20 liegen."
            )
        return value

    def validate_dietary_preferences(self, value):
        return self._validate_selection(
            value,
            DIETARY_PREFERENCES,
            "Ernährungspräferenz",
        )

    def validate_favorite_cuisines(self, value):
        return self._validate_selection(
            value,
            FAVORITE_CUISINES,
            "Lieblingsküche",
        )

    @staticmethod
    def _validate_selection(value, allowed, label):
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise serializers.ValidationError(
                f"{label} muss als Liste übermittelt werden."
            )

        invalid = [item for item in value if item not in allowed]
        if invalid:
            raise serializers.ValidationError(
                f"Unbekannte Auswahl: {', '.join(invalid)}"
            )

        return list(dict.fromkeys(value))
