from rest_framework.serializers import ModelSerializer

from core.models import Recipe


class RecipeSerializer(ModelSerializer):
    """Serializer for the recipe object"""

    class Meta:
        model = Recipe
        fields = ("id", "title", "time_minutes", "price", )
        read_only_fields = ("id",)
