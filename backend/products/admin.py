from django.contrib import admin

from .models import (
    IngredientPriceReference, IngredientSearchMetric, Product, ProductAlias,
    ProductUnitConversion,
)


class ProductAliasInline(admin.TabularInline):
    model = ProductAlias
    extra = 0


class ProductUnitConversionInline(admin.TabularInline):
    model = ProductUnitConversion
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "canonical_name", "source", "is_recipe_ingredient",
        "has_complete_nutrition",
    )
    list_filter = ("source", "is_recipe_ingredient")
    search_fields = ("name", "canonical_name", "aliases__alias")
    inlines = (ProductAliasInline, ProductUnitConversionInline)


@admin.register(ProductAlias)
class ProductAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "product", "source")
    list_filter = ("source",)
    search_fields = ("alias", "normalized_alias", "product__name")


@admin.register(ProductUnitConversion)
class ProductUnitConversionAdmin(admin.ModelAdmin):
    list_display = ("product", "unit", "grams_per_unit", "confidence", "source", "is_active")
    list_filter = ("confidence", "unit", "is_active")
    search_fields = ("product__name", "unit", "source")


@admin.register(IngredientSearchMetric)
class IngredientSearchMetricAdmin(admin.ModelAdmin):
    list_display = (
        "display_query", "context", "search_count", "zero_result_count",
        "selection_count", "last_selected_product", "review_status", "last_seen_at",
    )
    list_filter = ("context", "review_status")
    search_fields = ("display_query", "normalized_query", "last_selected_product__name")
    readonly_fields = (
        "normalized_query", "display_query", "context", "search_count",
        "zero_result_count", "selection_count", "last_result_count",
        "last_selected_rank", "last_selected_product", "selection_counts",
        "first_seen_at", "last_seen_at",
    )


admin.site.register(IngredientPriceReference)
