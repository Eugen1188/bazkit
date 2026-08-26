from django.urls import path

from .views import (
    WeeklyPlanEntryDetailAPIView,
    WeeklyPlanEntryListCreateAPIView,
    WeeklyPlanGenerateAPIView,
    WeeklyPlanShoppingListAPIView,
)


urlpatterns = [
    path(
        "entries/",
        WeeklyPlanEntryListCreateAPIView.as_view(),
        name="weekly-plan-entry-list-create",
    ),
    path(
        "entries/<int:pk>/",
        WeeklyPlanEntryDetailAPIView.as_view(),
        name="weekly-plan-entry-detail",
    ),
    path(
        "generate/",
        WeeklyPlanGenerateAPIView.as_view(),
        name="weekly-plan-generate",
    ),
    path(
        "shopping-list/",
        WeeklyPlanShoppingListAPIView.as_view(),
        name="weekly-plan-shopping-list",
    ),
]

