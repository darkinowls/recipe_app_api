from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core import models
from recipe import serializers


# Create your views here.


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""
    serializer_class = serializers.RecipeSerializer
    queryset: QuerySet = models.Recipe.objects.all()
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        recipes = self.queryset.filter(user=self.request.user)
        return recipes.order_by("-id")
