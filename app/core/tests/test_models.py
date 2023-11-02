from django.test import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        email = "email1@example.com"
        password = "testpass123"

        a: AbstractUser = get_user_model()

        user = a.objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        a: AbstractUser = get_user_model()

        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
        ]
        for email, example in sample_emails:
            user = a.objects.create_user(email, "samplepass")
            self.assertEqual(user.email, example)

    def test_new_user_invalid_email(self):
        a: AbstractUser = get_user_model()

        with self.assertRaises(ValueError):
            a.objects.create_user('', "samplepass")

    def test_create_new_superuser(self):
        a: AbstractUser = get_user_model()

        user = a.objects.create_superuser(
            'testsuper@exmaple.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


