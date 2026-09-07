from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import User, UserSettings


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://testserver",
)
class UserSettingsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="person@example.com",
            email="person@example.com",
            first_name="Erika",
            last_name="Muster",
            password="Passwort123",
        )
        self.client.force_authenticate(self.user)

    def test_me_returns_authenticated_profile(self):
        response = self.client.get("/users/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "person@example.com")
        self.assertEqual(response.data["first_name"], "Erika")

    def test_profile_can_be_updated(self):
        response = self.client.patch(
            "/users/me/",
            {
                "first_name": "Eva",
                "last_name": "Beispiel",
                "email": "eva@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Eva")
        self.assertEqual(self.user.email, "person@example.com")
        self.assertEqual(self.user.pending_email, "eva@example.com")
        self.assertEqual(len(mail.outbox), 1)

        verify_response = self.client.post(
            "/users/verify-email/",
            {"token": str(self.user.email_verification_token)},
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "eva@example.com")
        self.assertEqual(self.user.username, "eva@example.com")
        self.assertEqual(self.user.pending_email, "")

    def test_settings_are_created_and_persisted(self):
        response = self.client.get("/users/me/settings/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

        response = self.client.patch(
            "/users/me/settings/",
            {
                "recipe_default_portions": 4,
                "shopping_default_unit": "kg",
                "dietary_preferences": ["vegetarian", "high_protein"],
                "appearance": "dark",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.recipe_default_portions, 4)
        self.assertEqual(settings.appearance, "dark")

    def test_password_change_requires_current_password(self):
        response = self.client.post(
            "/users/me/change-password/",
            {
                "current_password": "falsch",
                "new_password": "NeuPasswort123",
                "new_password2": "NeuPasswort123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/users/me/change-password/",
            {
                "current_password": "Passwort123",
                "new_password": "NeuPasswort123",
                "new_password2": "NeuPasswort123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NeuPasswort123"))

    def test_registration_requires_and_records_terms_acceptance(self):
        payload = {
            "first_name": "Neu",
            "last_name": "Nutzer",
            "email": "neu@example.com",
            "password": "Passwort123",
            "password2": "Passwort123",
        }

        response = self.client.post("/users/register/", payload, format="json")
        self.assertEqual(response.status_code, 400)

        payload["accept_terms"] = True
        response = self.client.post("/users/register/", payload, format="json")
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="neu@example.com")
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertEqual(user.terms_version, "2026-09-05")
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.email_verification_token)
        self.assertEqual(len(mail.outbox), 1)

        login_response = self.client.post(
            "/users/login/",
            {"email": "neu@example.com", "password": "Passwort123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 400)

        verify_response = self.client.post(
            "/users/verify-email/",
            {"token": str(user.email_verification_token)},
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.email_verified_at)

    @patch("users.views.upload_avatar", return_value="avatars/1/profile.webp")
    def test_profile_avatar_can_be_uploaded_and_removed(self, upload_mock):
        image = SimpleUploadedFile(
            "avatar.png",
            b"image-content",
            content_type="image/png",
        )
        response = self.client.put(
            "/users/me/avatar/",
            {"avatar": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_key, "avatars/1/profile.webp")
        upload_mock.assert_called_once()

        with patch("users.views.delete_avatar") as delete_mock:
            response = self.client.delete("/users/me/avatar/")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_key, "")
        delete_mock.assert_called_once_with("avatars/1/profile.webp")
