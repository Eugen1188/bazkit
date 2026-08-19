from django.urls import path

from .views import (
    ProductSearchAPIView,
    ExternalProductSearchAPIView,
)


urlpatterns = [

    path(
        "search/",
        ProductSearchAPIView.as_view(),
        name="product-search"
    ),

    path(
        "external-search/",
        ExternalProductSearchAPIView.as_view(),
        name="product-external-search"
    ),

]