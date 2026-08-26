from django.urls import path

from .views import (
    ExternalProductSearchAPIView,
    ProductPriceEstimateAPIView,
    ProductSearchAPIView,
    SaveExternalProductAPIView,
)

urlpatterns = [
    path("search/", ProductSearchAPIView.as_view(), name="product-search"),
    path("price-estimate/", ProductPriceEstimateAPIView.as_view(), name="product-price-estimate"),
    path("external-search/", ExternalProductSearchAPIView.as_view(), name="product-external-search"),
    path("save-external/", SaveExternalProductAPIView.as_view(), name="product-save-external"),
]
