from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import Recipe, Tag, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(ModelSerializer):
    """Serializer for the recipe object"""
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ("id", "title", "time_minutes", "price", "link", "tags",)
        read_only_fields = ("id",)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user: User = self.context["request"].user
        for tag in tags:
            new_tag, _ = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(new_tag)
        return recipe

    def update(self, instance: Recipe, validated_data: dict):
        """Update a recipe"""
        tags = validated_data.pop("tags", [])
        recipe = super().update(instance, validated_data)
        recipe.tags.clear()
        auth_user: User = self.context["request"].user
        for tag in tags:
            new_tag, _ = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(new_tag)
        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe detail object"""

    class Meta(RecipeSerializer.Meta):
        fields = (*RecipeSerializer.Meta.fields, "description",)
