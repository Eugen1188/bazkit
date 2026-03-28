from django.urls import path
from .views import SavedListListCreateView, SavedListDetailView, ShoppingListListCreateView, ShoppingListDetailView, AddSavedListToShoppingListView, AddRecipeToShoppingListView

urlpatterns = [
    path('saved-lists/', SavedListListCreateView.as_view(), name='saved-list-list-create'),
    path('saved-lists/<int:pk>/', SavedListDetailView.as_view(), name='saved-list-detail'),
    path("shopping-lists/", ShoppingListListCreateView.as_view()),
    path("shopping-lists/<int:pk>/", ShoppingListDetailView.as_view()),
    path("shopping-lists/<int:shopping_list_id>/add-saved-list/", AddSavedListToShoppingListView.as_view()),
    path("shopping-lists/<int:shopping_list_id>/add-recipe/", AddRecipeToShoppingListView.as_view()),
]