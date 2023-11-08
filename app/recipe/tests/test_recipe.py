from _decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Recipe
from core.models import User
from recipe.serializers import RecipeSerializer

RECIPE_URL = reverse("recipe:recipe-list")


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": Decimal(5.00)
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the recipe model"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_is_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, 401)


class PrivateRecipeApiTests(TestCase):
    """Test the recipe model"""

    def setUp(self):
        self.client = APIClient()
        factory: User = get_user_model()
        self.user = factory.objects.create_user(
            email="user123@example.com",
            password="testpass",
        )
        self.client.force_authenticate(self.user)

    def test_return_recipes(self):
        """Test that recipes are returned"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, 200)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        factory: User = get_user_model()
        other = factory.objects.create_user(
            email="other@example.com",
            password="testpass",

        )
        create_recipe(user=other)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, 200)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
