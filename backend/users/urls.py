from django.urls import path
from .views import RegisterView, UserDetailView, UserListView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", UserDetailView.as_view(), name="user-detail"),
    path("user-list/", UserListView.as_view(), name="user-list"),
    ]