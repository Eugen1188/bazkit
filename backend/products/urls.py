from django.urls import path

from .views import (
    ExternalProductSearchAPIView,
    IngredientSearchFeedbackAPIView,
    ProductPriceEstimateAPIView,
    ProductSearchAPIView,
    SaveExternalProductAPIView,
)

urlpatterns = [
    path("search/", ProductSearchAPIView.as_view(), name="product-search"),
    path("search-feedback/", IngredientSearchFeedbackAPIView.as_view(), name="ingredient-search-feedback"),
    path("price-estimate/", ProductPriceEstimateAPIView.as_view(), name="product-price-estimate"),
    path("external-search/", ExternalProductSearchAPIView.as_view(), name="product-external-search"),
    path("save-external/", SaveExternalProductAPIView.as_view(), name="product-save-external"),
]
