import os.path
import tempfile

from _decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from core.models import User
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

from PIL import Image


def detail_url(recipe_id: int):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def get_image_upload_url(recipe_id: int):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_user(email, password, **params) -> User:
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password, **params)


def create_recipe(user, **params) -> Recipe:
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
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, 401)


class PrivateRecipeApiTests(TestCase):
    """Test the recipe model"""

    def setUp(self):
        self.client = APIClient()
        factory: User = get_user_model()

        self.user = create_user(email="user123@example.com",
                                password="testpass", )

        self.client.force_authenticate(self.user)

    def test_return_recipes(self):
        """Test that recipes are returned"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, 200)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        factory: User = get_user_model()
        other = create_user(email="limit@example.com",
                            password="testpass", )
        create_recipe(user=other)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, 200)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving a recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal(5.00),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test updating a recipe with patch"""
        link = "https://example.com"
        recipe = create_recipe(user=self.user,
                               title="Sample recipe",
                               link=link)
        payload = {"title": "Sample recipe updated"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

        self.assertEqual(recipe.link, link)

    def test_full_update(self):
        recipe = create_recipe(user=self.user,
                               title="Sample recipe",
                               link="https://example.com",
                               description="Sample description",
                               )
        payload = {
            "title": "Sample recipe updated",
            "time_minutes": 30,
            "price": Decimal(5.00),
            "description": "Sample description updated",
            "link": "https://example.com/updated",
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(v, getattr(recipe, k))
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_user_and_other_user(self):
        new_user = create_user(email="other@example.com",
                               password="testpass", )
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal(5.00),
            "tags": [{'name': "vegan"}, {'name': "dessert"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)

    def test_create_recipe_with_old_tag(self):

        tag1 = Tag.objects.create(user=self.user, name="vegan")

        payload = {
            "title": "Sample recipe",
            "time_minutes": 10,
            "price": Decimal(5.00),
            "tags": [{"name": "vegan"}, {"name": "dessert"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(id=res.data["id"])
        self.assertEqual(recipes[0].tags.count(), 2)
        self.assertIn(tag1, recipes[0].tags.all())

    def test_patch_recipe_with_tags(self):
        recipe = create_recipe(user=self.user)
        payload = {
            "tags": [{"name": "Lunch"}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, Tag.objects.all())

    def test_patch_assign_tag(self):
        tag_b = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_b)

        tag_l = Tag.objects.create(user=self.user, name="Lunch")
        payload = {
            "tags": [{"name": "Lunch"}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_l, recipe.tags.all())
        self.assertNotIn(tag_b, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag_b = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_b)
        payload = {
            "tags": []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag_b, recipe.tags.all())

    def test_recipe_with_new_ingredients(self):
        payload = {
            "title": "Sample recipe",
            "time_minutes": 10,
            "price": Decimal(5.00),
            "ingredients": [{"name": "Salt"}, {"name": "Pepper"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("ingredients", res.data)
        self.assertEqual(len(res.data["ingredients"]), 2)

    def test_create_recipe_with_old_ingredients(self):
        Ingredient.objects.create(user=self.user, name="Salt")
        payload = {
            "title": "Sample recipe",
            "time_minutes": 10,
            "price": Decimal(5.00),
            "ingredients": [{"name": "Salt"}, {"name": "Pepper"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertIn("ingredients", res.data)
        self.assertEqual(recipe.ingredients.count(), 2)
        ingredients = Ingredient.objects.all()
        self.assertIn(ingredients[0], recipe.ingredients.all())

    def test_patch_recipe_with_ingredients(self):
        recipe = create_recipe(user=self.user)
        payload = {
            "ingredients": [{"name": "Salt"}, {"name": "Pepper"}]
        }
        res = self.client.patch(detail_url(recipe.id), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("ingredients", res.data)
        self.assertEqual(len(res.data["ingredients"]), 2)
        self.assertEqual(recipe.title, res.data["title"])

    def test_update_recipe_assign_ingredient(self):
        i1 = Ingredient.objects.create(user=self.user, name="Salt")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(i1)
        i2 = Ingredient.objects.create(user=self.user, name="Pepper")
        payload = {
            "ingredients": [{"name": "Pepper"}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(i2, recipe.ingredients.all())
        self.assertNotIn(i1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        i1 = Ingredient.objects.create(user=self.user, name="Salt")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(i1)
        url = detail_url(recipe.id)
        res = self.client.delete(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(i1, recipe.ingredients.all())


class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="self@exmapl.com", password="testpass")
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = get_image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img: Image = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {
                "image": image_file
            }
            res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad(self):
        url = get_image_upload_url(self.recipe.id)
        payload = {
            "image": "notimage"
        }
        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
