from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import Recipe, Tag, User, Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the ingredient object"""

    class Meta:
        model = Ingredient
        fields = ("id", "name",)
        read_only_fields = ("id",)


class RecipeSerializer(ModelSerializer):
    """Serializer for the recipe object"""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ("id", "title", "time_minutes", "price", "link", "tags", "ingredients",)
        read_only_fields = ("id",)

    def __get_or_create_tag(self, tags: list[dict], recipe: Recipe) -> Recipe:
        """Get or create a tag"""
        auth_user: User = self.context["request"].user
        for tag in tags:
            new_tag, _ = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(new_tag)
        return recipe

    def __get_or_create_ingredient(self, ingredients: list[dict], recipe: Recipe) -> Recipe:
        """Get or create an ingredient"""
        auth_user: User = self.context["request"].user
        for ingredient in ingredients:
            new_ingredient, _ = Ingredient.objects.get_or_create(user=auth_user, **ingredient)
            recipe.ingredients.add(new_ingredient)
        return recipe

    def create(self, validated_data: dict):
        """Create a recipe"""
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self.__get_or_create_tag(tags, recipe)
        self.__get_or_create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance: Recipe, validated_data: dict):
        """Update a recipe"""
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = super().update(instance, validated_data)
        recipe.tags.clear()
        recipe.ingredients.clear()
        self.__get_or_create_ingredient(ingredients, recipe)
        self.__get_or_create_tag(tags, recipe)
        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe detail object"""

    class Meta(RecipeSerializer.Meta):
        fields = (*RecipeSerializer.Meta.fields, "description",)


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes"""

    class Meta:
        model = Recipe
        fields = ("id", "image",)
        read_only_fields = ("id",)
        extra_kwargs = {"image": {"required": True}}
