from unittest import TestCase
from jug_ee.life_cycle_assessment.envelope_emission\
    import EnvelopeEmission


class TestEnvelopeEmission(TestCase):
    def setUp(self):
        self.envelope = EnvelopeEmission(230, 0.2, 13, 2.3)

    def test_calculate_envelope_emission(self):
        expected = 230 * 0.2 * 13 * 2.3
        self.assertEqual(self.envelope.calculate_envelope_emission(), expected)
