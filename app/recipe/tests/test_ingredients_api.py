from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def get_detail_url(i_id):
    return reverse("recipe:ingredient-detail", args=[i_id])


def create_user(email, password, **params):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password, **params)


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="hello@exampl.com", password="testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="Beer")

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        i: Ingredient = Ingredient.objects.all()

        serializer = IngredientSerializer(i, many=True)
        self.assertEqual(serializer.data, res.data)

    def test_ingredients_limited(self):
        """Test that ingredients are limited to authenticated user"""
        user2 = create_user(email="user2@exmaple.com", password="testpass")
        Ingredient.objects.create(user=user2, name="Water")
        i = Ingredient.objects.create(user=self.user, name="Beer")

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], i.name)

    def test_patch_ingredient(self):
        """Test patch an ingredient"""
        i = Ingredient.objects.create(user=self.user, name="Beer")
        payload = {"name": "Whiskey"}
        res = self.client.patch(get_detail_url(i.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        i.refresh_from_db()
        self.assertEqual(i.name, payload.get("name"))

    def test_delete_ingredient(self):
        """Test delete an ingredient"""
        i = Ingredient.objects.create(user=self.user, name="Beer")
        res = self.client.delete(get_detail_url(i.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.count(), 0)

    def test_filter_ingredients_assigned_to_recipes(self):
        i1 = Ingredient.objects.create(user=self.user, name="Beer")
        i2 = Ingredient.objects.create(user=self.user, name="Whiskey")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe",
            time_minutes=5,
            price=5.00
        )
        recipe.ingredients.add(i1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(i1)
        s2 = IngredientSerializer(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        i = Ingredient.objects.create(user=self.user, name="Beer")
        Ingredient.objects.create(user=self.user, name="Whiskey")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe 1",
            time_minutes=5,
            price=5.00
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe 2",
            time_minutes=5,
            price=5.00
        )
        recipe1.ingredients.add(i)
        recipe2.ingredients.add(i)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], i.name)
        self.assertEqual(res.data[0]["id"], i.id)
