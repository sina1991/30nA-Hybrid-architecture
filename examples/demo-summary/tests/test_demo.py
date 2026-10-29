import unittest
from demo_worker import run


class SummaryTests(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(run({'values':[10,20,30]},{}),
            {'count':3,'sum':60,'min':10,'max':30,'mean':20.0})

    def test_invalid_input_is_rejected(self):
        for values in ([],[True],['10'],[float('inf')],[1e13]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                run({'values':values},{})
