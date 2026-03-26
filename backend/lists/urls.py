from django.urls import path
from .views import SavedListListCreateView, SavedListDetailView

urlpatterns = [
    path('saved-lists/', SavedListListCreateView.as_view(), name='saved-list-list-create'),
    path('saved-lists/<int:pk>/', SavedListDetailView.as_view(), name='saved-list-detail'),
]