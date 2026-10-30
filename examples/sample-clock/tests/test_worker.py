import unittest
from worker import run


class ClockWorkerTests(unittest.TestCase):
    def test_output_has_utc_and_integer_timestamp(self):
        result = run({}, {})
        self.assertTrue(result['utc'].endswith('Z'))
        self.assertIsInstance(result['unix_seconds'], int)
