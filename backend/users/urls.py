from django.urls import path
from .views import (
    ChangePasswordView,
    LoginUserView,
    RegisterUserView,
    ResendVerificationEmailView,
    UserAvatarView,
    UserMeView,
    UserSettingsView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    path("me/", UserMeView.as_view(), name="me"),
    path("me/avatar/", UserAvatarView.as_view(), name="avatar"),
    path("me/settings/", UserSettingsView.as_view(), name="settings"),
    path(
        "me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
]
