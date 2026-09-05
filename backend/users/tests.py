from rest_framework.test import APITestCase

from .models import User, UserSettings


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
        self.assertEqual(self.user.username, "eva@example.com")

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
