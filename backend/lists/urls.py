from django.urls import path

from .views import (
    SavedListListCreateAPIView,
    SavedListDetailAPIView,
    SavedListItemDetailAPIView,
    ShoppingListAPIView,
    ShoppingListItemCreateAPIView,
    ShoppingListItemDetailAPIView,
    AddSavedListToShoppingListAPIView
)


urlpatterns = [

    # SAVED LISTS

    path(
        "saved-lists/",
        SavedListListCreateAPIView.as_view(),
        name="saved-list-list-create"
    ),

    path(
        "saved-lists/<int:pk>/",
        SavedListDetailAPIView.as_view(),
        name="saved-list-detail"
    ),

    path(
        "saved-lists/<int:list_id>/items/<int:item_id>/",
        SavedListItemDetailAPIView.as_view(),
        name="saved-list-item-detail"
    ),


    # SHOPPING LIST

    path(
        "shopping-list/",
        ShoppingListAPIView.as_view(),
        name="shopping-list"
    ),

    path(
        "shopping-list/items/",
        ShoppingListItemCreateAPIView.as_view(),
        name="shopping-list-item-create"
    ),

    path(
        "shopping-list/items/<int:item_id>/",
        ShoppingListItemDetailAPIView.as_view(),
        name="shopping-list-item-detail"
    ),

    path(
        "shopping-list/add-saved-list/<int:saved_list_id>/",
        AddSavedListToShoppingListAPIView.as_view(),
        name="shopping-list-add-saved-list"
    ),

]