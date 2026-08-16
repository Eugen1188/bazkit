"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "users/",
        include("users.urls")
    ),

    path(
        "lists/",
        include("lists.urls")
    ),

    path(
        "recipes/",
        include("recipes.urls")
    ),

    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
]