from rest_framework import serializers
from .models import SavedList, SavedListItem

class SavedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedList
        fields = ['id', 'title', 'created_at']
        read_only_fields = ['id', 'created_at']