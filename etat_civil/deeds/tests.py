from django.test import TestCase
from deeds.models import get_date_of_birth


class ImportTestCase(TestCase):
    def test_get_date_of_birth(self):
        value = '23/08/1827'

        self.assertEqual(
            1802, get_date_of_birth(value, 25).year)
        self.assertRaises(
            AssertionError, get_date_of_birth, deed_date=None, age=25)
        self.assertRaises(
            AssertionError, get_date_of_birth, deed_date=value, age=None)
