import unittest
from worker import run


class MathWorkerTests(unittest.TestCase):
    def test_summary_and_configuration(self):
        self.assertEqual(run({'values': [1, 2, 3]}, {'multiplier': 2})['scaled_sum'], 12)

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            run({'values': [True]}, {})
