from abc import ABC

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import models
from recipe import serializers


# Create your views here.


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("tags",
                             type=OpenApiTypes.STR,
                             description="Filter recipes by tags. Enter comma seperated values in GET request"),
            OpenApiParameter("ingredients",
                             type=OpenApiTypes.STR,
                             description="Filter recipes by ingredients id. " +
                                         "Enter comma seperated values in GET request"),
        ],
    ),
)
class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset: QuerySet = models.Recipe.objects.all()
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def __params_to_ints(self, qs: str) -> frozenset[int]:
        """Convert an id string to a set of integers"""
        if qs is None:
            return frozenset()
        try:
            return frozenset([int(str_id) for str_id in qs.split(",")])
        except ValueError:
            return frozenset()

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        tags_or_none: str = self.request.query_params.get('tags')
        ingredients_or_none: str = self.request.query_params.get('ingredients')

        tags_ids: frozenset[int] = self.__params_to_ints(tags_or_none)
        ingredients_ids: frozenset[int] = self.__params_to_ints(ingredients_or_none)

        queryset = self.queryset
        if len(tags_ids) != 0:
            queryset = queryset.filter(tags__id__in=tags_ids)
        if len(ingredients_ids) != 0:
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)

        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "list":
            return serializers.RecipeSerializer
        if self.action == "upload_image":
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer: serializers.RecipeSerializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe: models.Recipe = self.get_object()
        serializer: serializers.RecipeImageSerializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("assigned_only",
                             type=OpenApiTypes.INT,
                             enum=[0, 1],
                             description="Filter tags by assigned recipes. Enter 1 or 0 in GET request"),
        ],
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet,
                            ABC):
    """Base viewset for user owned recipe attributes"""
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by("-name").distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.TagSerializer
    queryset: QuerySet = models.Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset: QuerySet = models.Ingredient.objects.all()
