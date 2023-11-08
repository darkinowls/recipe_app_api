from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "email": "success@example.com",
            "password": "test123",
            "name": "Test Name",
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["email"], payload["email"])
        self.assertNotIn("password", res.data)

    def test_user_exists_error(self):
        """Test creating a user that already exists fails"""
        payload = {
            "email": "fail@example.com",
            "password": "test123",
            "name": "Test Name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, 400)

    def test_password_is_too_short(self):
        """Test that the password must be more than 5 characters"""
        payload = {

            "email": "short@example.com",
            "password": "1",
            "name": "Test Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, 400)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {
            "email": "token@example.com",
            "password": "test123",
            "name": "Test Name",
        }

        create_user(**payload)
        payload = {
            "email": "token@example.com",
            "password": "test123",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", res.data)

    def test_bad_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email="badc@example.com", password="test123", name="Test Name")
        payload = {
            "email": "badc@example.com",
            "password": "wrong123"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", res)

    def test_token_blank_password(self):
        payload = {
            "email": "blank",
            "password": "",
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", res)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email="authed@example.com",
            password="test123",
            name="Test Name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data, {"name": self.user.name, "email": self.user.email}
        )

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            "name": "New Name",
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        # self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
