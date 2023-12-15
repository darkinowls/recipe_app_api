"""
Test for the health endpoint
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        url = reverse("health")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
