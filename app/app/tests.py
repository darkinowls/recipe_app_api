from django.test import SimpleTestCase

from . import calc


class CalcTest(SimpleTestCase):

    def test_add(self):
        """Test that values are added together"""
        res = calc.add(1, 3)
        self.assertEqual(res, 4)

    def test_subtract(self):
        """Test that values are subtracted and returned"""
        res = calc.subtract(5, 11)
        self.assertEqual(res, -6)
