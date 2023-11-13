from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import Tag, User, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email="asdasd@example.com", password="adsd23r", **params):
    """Create a sample user"""
    user: User = get_user_model()
    return user.objects.create_user(email, password, **params)


def detail_url(tag_id: int) -> str:
    """Return tag detail URL"""
    return reverse("recipe:tag-detail", args=[tag_id])


class PublicTagsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        user2 = create_user(email="dsa1@exmaple.com", password="sdadqw1")
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name="Test Tag")
        payload = {"name": "New Tag Name"}
        url = detail_url(tag.id)
        self.client.patch(url, payload)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name="Test Tag")
        self.assertEqual(Tag.objects.count(), 1)
        url = detail_url(tag.id)
        self.client.delete(url)
        self.assertEqual(Tag.objects.count(), 0)

    def test_filter_tags_assigned_to_recipes(self):
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(user=self.user,
                                       title="Coriander eggs on toast",
                                       time_minutes=10,
                                       price=10)
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_tag_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Lunch")
        recipe1 = Recipe.objects.create(user=self.user,
                                        title="Coriander eggs on toast",
                                        time_minutes=10,
                                        price=10)
        recipe2 = Recipe.objects.create(user=self.user,
                                        title="Pancakes",
                                        time_minutes=10,
                                        price=10)
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag1.name)
        self.assertEqual(res.data[0]["id"], tag1.id)
