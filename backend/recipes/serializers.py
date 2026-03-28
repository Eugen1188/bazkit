from rest_framework import serializers
from .models import Recipe, Ingredients

class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['id', 'name', 'quantity', 'unit']

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = Ingredients(many = True)
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'insctructions', 'created_at', 'ingredients']
        read_only_fields = ['id']
        
    def create(self, validated_data):
        ingredients_data = validated_data.pop('incredients', [])
        user = self.context['request'].user
        
        recipe = Recipe.objects.create(user=user, **validated_data)
        
        for ingredient_data in ingredients_data:
            Recipe.objects.create(
                recipe=recipe,
                **ingredient_data 
            )
            
        return recipe