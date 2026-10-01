from django.contrib import admin

from django.urls import (
    include,
    path,
)

from .views import health_check
from users.views import ThrottledTokenRefreshView


urlpatterns = [

    path(
        "health/",
        health_check,
        name="health-check"
    ),

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "users/",
        include(
            "users.urls"
        )
    ),

    path(
        "lists/",
        include(
            "lists.urls"
        )
    ),

    path(
        "recipes/",
        include(
            "recipes.urls"
        )
    ),

    path(
        "products/",
        include(
            "products.urls"
        )
    ),

    path(
        "planner/",
        include(
            "planner.urls"
        )
    ),

    path(
        "community/",
        include(
            "community.urls"
        )
    ),

    path(
        "monitoring/",
        include(
            "monitoring.urls"
        )
    ),

    path(
        "api/token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token_refresh"
    ),

]
