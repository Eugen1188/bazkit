from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
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

    def test_password_change_invalidates_existing_refresh_token(self):
        login_response = self.client.post(
            "/users/login/",
            {"email": self.user.email, "password": "Passwort123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)

        change_response = self.client.post(
            "/users/me/change-password/",
            {
                "current_password": "Passwort123",
                "new_password": "SicherNeu123",
                "new_password2": "SicherNeu123",
            },
            format="json",
        )
        self.assertEqual(change_response.status_code, 200)

        refresh_response = self.client.post(
            "/api/token/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)

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
        self.assertEqual(user.terms_version, "2026-10-01")
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

    @patch("users.signals.delete_avatar")
    def test_account_deletion_removes_user_settings_and_uploaded_avatar(self, delete_mock):
        self.user.avatar_key = "avatars/1/profile.webp"
        self.user.save(update_fields=["avatar_key"])
        UserSettings.objects.create(user=self.user, appearance="dark")
        user_id = self.user.id

        response = self.client.delete("/users/me/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(UserSettings.objects.filter(user_id=user_id).exists())
        delete_mock.assert_called_once_with("avatars/1/profile.webp")

    def test_password_reset_does_not_reveal_accounts_and_changes_password(self):
        unknown_response = self.client.post(
            "/users/password-reset/",
            {"email": "unknown@example.com"},
            format="json",
        )
        self.assertEqual(unknown_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(
            "/users/password-reset/",
            {"email": self.user.email},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        query = parse_qs(urlparse(mail.outbox[0].body.splitlines()[4]).query)

        confirm_response = self.client.post(
            "/users/password-reset/confirm/",
            {
                "uid": query["uid"][0],
                "token": query["token"][0],
                "new_password": "GanzNeu123",
                "new_password2": "GanzNeu123",
            },
            format="json",
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("GanzNeu123"))

        reused_response = self.client.post(
            "/users/password-reset/confirm/",
            {
                "uid": query["uid"][0],
                "token": query["token"][0],
                "new_password": "NochEinmal123",
                "new_password2": "NochEinmal123",
            },
            format="json",
        )
        self.assertEqual(reused_response.status_code, 400)

    def test_contact_form_sends_message_with_safe_reply_to(self):
        response = self.client.post(
            "/users/contact/",
            {
                "name": "Erika Muster",
                "email": "erika@example.com",
                "subject": "Frage zu meinem Konto",
                "message": "Bitte helft mir bei meinem Bazkit-Konto.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["kontakt@ferchow-eugen.de"])
        self.assertEqual(mail.outbox[0].reply_to, ["erika@example.com"])

    @override_settings(AUTH_THROTTLES_ENABLED=True)
    def test_login_is_rate_limited(self):
        self.client.force_authenticate(user=None)
        cache.clear()
        responses = [
            self.client.post(
                "/users/login/",
                {"email": "unknown@example.com", "password": "Falsch123"},
                format="json",
            )
            for _ in range(11)
        ]

        self.assertTrue(all(response.status_code == 400 for response in responses[:10]))
        self.assertEqual(responses[-1].status_code, 429)
        cache.clear()
