from django.test import TestCase

from .models import Match

# Create your tests here.
class MatchMethodTests(TestCase):

    def test_only_return_completed_matches(self):
    """
    completed()
    """
