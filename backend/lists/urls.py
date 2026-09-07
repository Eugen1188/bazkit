from django.urls import path

from .views import (
    SavedListListCreateAPIView,
    SavedListDetailAPIView,
    SavedListItemDetailAPIView,
    SavedListItemToggleAPIView,
    SavedListCollaborationAPIView,
    SavedListInvitationManageAPIView,
    SavedListMemberAPIView,
    SavedListLeaveAPIView,
    SavedListInvitationAPIView,
    ShoppingListAPIView,
    ShoppingListItemCreateAPIView,
    ShoppingListItemDetailAPIView,
    AddSavedListToShoppingListAPIView,
    AddRecipeToShoppingListAPIView
)


urlpatterns = [

    # ==========================
    # SAVED LISTS
    # ==========================

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

    path(
        "saved-lists/<int:list_id>/items/<int:item_id>/toggle/",
        SavedListItemToggleAPIView.as_view(),
        name="saved-list-item-toggle"
    ),

    path(
        "saved-lists/<int:list_id>/collaboration/",
        SavedListCollaborationAPIView.as_view(),
        name="saved-list-collaboration"
    ),

    path(
        "saved-lists/<int:list_id>/invitations/<int:invitation_id>/",
        SavedListInvitationManageAPIView.as_view(),
        name="saved-list-invitation-manage"
    ),

    path(
        "saved-lists/<int:list_id>/members/<int:membership_id>/",
        SavedListMemberAPIView.as_view(),
        name="saved-list-member"
    ),

    path(
        "saved-lists/<int:list_id>/leave/",
        SavedListLeaveAPIView.as_view(),
        name="saved-list-leave"
    ),

    path(
        "saved-list-invitations/<uuid:token>/",
        SavedListInvitationAPIView.as_view(),
        name="saved-list-invitation"
    ),


    # ==========================
    # SHOPPING LIST
    # ==========================

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

    path(
        "shopping-list/add-recipe/<int:recipe_id>/",
        AddRecipeToShoppingListAPIView.as_view(),
        name="shopping-list-add-recipe"
    ),
]
