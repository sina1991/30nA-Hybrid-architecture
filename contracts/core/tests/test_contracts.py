import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CoreContractTests(unittest.TestCase):
    def load_contract(self, relative):
        path = ROOT / relative
        with path.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        self.assertIsInstance(data, dict, str(path))
        self.assertIn("contract", data)
        self.assertIn("contract_version", data)
        self.assertIn("status", data)
        return data

    def test_all_yaml_contracts_parse(self):
        paths = sorted(ROOT.rglob("*.yaml"))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=str(path)):
                with path.open(encoding="utf-8") as stream:
                    data = yaml.safe_load(stream)
                self.assertIsInstance(data, dict)
                for field in ("contract", "contract_version", "status"):
                    self.assertIn(field, data)

    def test_resource_id_is_not_globally_required(self):
        data = self.load_contract("identifiers/contract.yaml")
        self.assertNotIn("required", data["identifiers"]["resource_id"])
        self.assertEqual(
            data["identifiers"]["resource_id"]["required_by"],
            "resource-owning-contract",
        )

    def test_operation_transitions_reference_known_statuses(self):
        data = self.load_contract("status/operation.yaml")
        statuses = data["statuses"]
        transitions = data["transitions"]
        self.assertEqual(set(statuses), set(transitions))

        for source, targets in transitions.items():
            with self.subTest(source=source):
                self.assertIsInstance(targets, list)
                for target in targets:
                    self.assertIn(target, statuses)
                if statuses[source]["terminal"]:
                    self.assertEqual(targets, [])

        self.assertEqual(
            set(transitions["accepted"]),
            {"running", "failed", "cancelled"},
        )
        self.assertEqual(
            set(transitions["running"]),
            {"succeeded", "failed", "cancelled"},
        )

    def test_envelope_requires_version_and_payload(self):
        data = self.load_contract("envelope/contract.yaml")
        fields = data["fields"]
        self.assertTrue(fields["contract_version"]["required"])
        self.assertTrue(fields["payload"]["required"])
        self.assertFalse(fields["correlation_id"]["required"])

    def test_versioning_domains_are_independent(self):
        data = self.load_contract("versioning/policy.yaml")
        domains = data["version_domains"]
        for name in ("shared_contract", "api", "implementation", "calculation"):
            self.assertIn(name, domains)
        self.assertTrue(data["compatibility"]["incompatible_version_behavior"])


if __name__ == "__main__":
    unittest.main()
