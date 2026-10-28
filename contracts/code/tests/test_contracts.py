import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CodeContractTests(unittest.TestCase):
    def load_contract(self, relative):
        path = ROOT / relative
        with path.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        self.assertIsInstance(data, dict, str(path))
        self.assertIn("contract", data)
        self.assertIn("contract_version", data)
        self.assertIn(data["status"], {"draft", "approved"})
        return data

    def test_all_yaml_contracts_parse(self):
        paths = sorted(ROOT.rglob("*.yaml"))
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            with self.subTest(path=str(path)):
                with path.open(encoding="utf-8") as stream:
                    data = yaml.safe_load(stream)
                self.assertIsInstance(data, dict)
                for key in ("contract", "contract_version", "status"):
                    self.assertIn(key, data)

    def test_python_is_the_only_language(self):
        data = self.load_contract("source/contract.yaml")
        self.assertEqual(data["source"]["language"]["allowed_values"], ["python"])

    def test_build_pipeline_contains_required_stages(self):
        data = self.load_contract("build/contract.yaml")
        stages = data["pipeline"]["stages"]
        for stage in (
            "inspect_archive",
            "verify_source_hash",
            "validate_archive_paths",
            "normalize_working_copy",
            "syntax_check",
            "dependency_check",
            "contract_check",
            "test",
            "package",
            "hash",
        ):
            self.assertIn(stage, stages)

    def test_artifact_requires_integrity_and_calculation_identity(self):
        data = self.load_contract("artifact/contract.yaml")
        fields = data["artifact"]
        for field in (
            "source_version",
            "source_hash",
            "build_version",
            "artifact_hash",
            "calculation_version",
            "validation_status",
        ):
            self.assertTrue(fields[field]["required"], field)

    def test_release_requires_passed_validation(self):
        data = self.load_contract("release/contract.yaml")
        self.assertIn(
            "Only an artifact with validation_status passed may be published.",
            data["rules"],
        )

    def test_api_does_not_define_direct_database_access(self):
        data = self.load_contract("api/contract.yaml")
        self.assertTrue(
            any("No operation may provide direct access to Data Manager storage."
                in rule for rule in data["rules"])
        )

    def test_version_domains_are_independent(self):
        data = self.load_contract("versioning/policy.yaml")
        domains = data["version_domains"]
        for name in (
            "source_version",
            "build_version",
            "artifact_version",
            "calculation_version",
            "shared_contract_version",
            "api_version",
        ):
            self.assertIn(name, domains)


if __name__ == "__main__":
    unittest.main()
