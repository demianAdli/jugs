from unittest import TestCase
from jug_ee.life_cycle_assessment.opening_emission\
    import OpeningEmission


class TestOpeningEmission(TestCase):
    def setUp(self):
        self.opening = OpeningEmission(230, 13)

    def test_calculate_opening_emission(self):
        expected = 230 * 13
        self.assertEqual(self.opening.calculate_opening_emission(), expected)
