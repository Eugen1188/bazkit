from django.urls import path

from .views import BrowserErrorView


urlpatterns = [
    path("browser-errors/", BrowserErrorView.as_view(), name="browser-errors"),
]
