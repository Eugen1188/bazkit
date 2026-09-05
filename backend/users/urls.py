from django.urls import path
from .views import (
    ChangePasswordView,
    LoginUserView,
    RegisterUserView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("me/", UserMeView.as_view(), name="me"),
    path("me/settings/", UserSettingsView.as_view(), name="settings"),
    path(
        "me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
]
