from rest_framework import serializers
from .models import SavedList, SavedListItem, ShoppingList, ShoppingListItem

class SavedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedList
        fields = ["id", "title", "created_at"]
        
class SavedListItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SavedListItem
        fields = ["id", "product", "product_name", "name", "quantity", "unit"]
        
    def validate(self, attrs):
        product = attrs.get("product")
        name = attrs.get("name", "").strip()
        if not product and not name:
            raise serializers.ValidationError("Either product or name must be provided.")
        
        return attrs
    
class SavedListDetailSerializer(serializers.ModelSerializer):
    items = SavedListItemSerializer(many=True, read_only=True)

    class Meta:
        model = SavedList
        fields = ["id", "title", "created_at", "items"]

# class SavedListItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SavedListItem
#         fields = ['id', 'product', 'name', 'quantity', 'unit']
#         read_only_fields = ['id']
        
# class SavedListSerializer(serializers.ModelSerializer):
#     items = SavedListItemSerializer(many = True, required=False)
#     class Meta:
#         model = SavedList
#         fields = ['id', 'title', 'created_at', 'items']
#         read_only_fields = ['id', 'created_at']
        
#     def create(self, validated_data):
#         items_data = validated_data.pop('items', [])
#         user = self.context['request'].user

#         saved_list = SavedList.objects.create(user=user, **validated_data)
        
#         for item_data in items_data:
#             SavedListItem.objects.create(
#                 saved_list=saved_list,
#                 **item_data
#         )
        
#         return saved_list

# class ShoppingListItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ShoppingListItem
#         fields = ['id', 'product', 'name', 'quantity', 'unit', 'is_checked']
#         read_only_fields = ['id']
        
# class ShoppingListSerializer(serializers.ModelSerializer):
#     items = ShoppingListItemSerializer(many=True, required=False)

#     class Meta:
#         model = ShoppingList
#         fields = ['id', 'title', 'created_at', 'items']
#         read_only_fields = ['id', 'created_at']

#     def create(self, validated_data):
#         items_data = validated_data.pop('items', [])
#         user = self.context['request'].user

#         shopping_list = ShoppingList.objects.create(user=user, **validated_data)

#         for item_data in items_data:
#             ShoppingListItem.objects.create(
#                 shopping_list=shopping_list,
#                 **item_data
#             )

#         return shopping_list
    
# class AddSavedListToShoppingListSerializer(serializers.Serializer):
#     saved_list_id = serializers.IntegerField()


# class AddRecipeToShoppingListSerializer(serializers.Serializer):
#     recipe_id = serializers.IntegerField()