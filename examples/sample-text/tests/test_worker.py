import unittest
from worker import run


class TextWorkerTests(unittest.TestCase):
    def test_transform(self):
        self.assertEqual(run({'text': 'hello'}, {'prefix': '>', 'uppercase': True})['text'], '>HELLO')

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            run({'text': 123}, {})
