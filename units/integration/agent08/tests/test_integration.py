import importlib.util
import pathlib
import unittest

FILE = pathlib.Path(__file__).resolve().parents[1] / 'agent08.py'
spec = importlib.util.spec_from_file_location('agent08', FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RealRuntimeTests(unittest.TestCase):
    def test_real_subprocess(self):
        integration = module.Integration(mode='demo')
        result = integration.execute_once()
        self.assertEqual(result.status, 'succeeded', result.error)
        self.assertEqual(result.result, 'modules OK')
        self.assertEqual(integration.snapshot()['source'], 'worker-runtime')

    def test_two_executions_are_distinct(self):
        integration = module.Integration(mode='demo')
        first = integration.execute_once()
        second = integration.execute_once()
        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertEqual(integration.snapshot()['sequence'], 2)


if __name__ == '__main__':
    unittest.main()
