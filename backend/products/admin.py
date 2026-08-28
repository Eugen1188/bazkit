from django.contrib import admin

from .models import IngredientPriceReference, Product, ProductAlias


class ProductAliasInline(admin.TabularInline):
    model = ProductAlias
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "canonical_name", "source", "is_recipe_ingredient",
        "has_complete_nutrition",
    )
    list_filter = ("source", "is_recipe_ingredient")
    search_fields = ("name", "canonical_name", "aliases__alias")
    inlines = (ProductAliasInline,)


@admin.register(ProductAlias)
class ProductAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "product", "source")
    list_filter = ("source",)
    search_fields = ("alias", "normalized_alias", "product__name")


admin.site.register(IngredientPriceReference)
