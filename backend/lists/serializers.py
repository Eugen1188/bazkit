from rest_framework import serializers
from .models import SavedList, SavedListItem

class SavedListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedListItem
        fields = ['id', 'product', 'custom_name', 'quantity']
        read_only_fields = ['id']
        
class SavedListSerializer(serializers.ModelSerializer):
    items = SavedListItemSerializer(many = True, required=False)
    class Meta:
        model = SavedList
        fields = ['id', 'title', 'created_at', 'items']
        read_only_fields = ['id', 'created_at']
        
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        user = self.context['request'].user

        saved_list = SavedList.objects.create(user=user, **validated_data)
        
        for item_data in items_data:
            SavedListItem.objects.create(
                saved_list=saved_list,
                **item_data
        )
        
        return saved_list