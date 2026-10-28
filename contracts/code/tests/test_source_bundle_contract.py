import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_contract(relative_path):
    with (ROOT / relative_path).open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class SourceBundleContractTests(unittest.TestCase):
    def test_source_requires_zip_and_exact_content_hash(self):
        source = load_contract("source/contract.yaml")
        fields = source["source"]

        self.assertEqual(fields["source_format"]["allowed_values"], ["zip"])
        self.assertEqual(fields["source_content"]["type"], "binary")
        self.assertEqual(fields["source_hash"]["algorithm"], "sha256")

    def test_entrypoint_and_schema_formats_are_explicit(self):
        source = load_contract("source/contract.yaml")
        fields = source["source"]

        self.assertEqual(fields["entrypoint"]["format"], "module:function")
        self.assertIn("JSON Schema", fields["input_schema"]["description"])
        self.assertIn("JSON Schema", fields["output_schema"]["description"])

    def test_build_verifies_original_source_before_processing(self):
        build = load_contract("build/contract.yaml")
        stages = build["pipeline"]["stages"]

        self.assertLess(stages.index("inspect_archive"), stages.index("verify_source_hash"))
        self.assertLess(stages.index("verify_source_hash"), stages.index("normalize_working_copy"))

    def test_artifact_tracks_source_and_artifact_hash_algorithms(self):
        artifact = load_contract("artifact/contract.yaml")["artifact"]

        self.assertEqual(artifact["source_hash"]["algorithm"], "sha256")
        self.assertEqual(artifact["artifact_hash"]["algorithm"], "sha256")
        self.assertEqual(artifact["entrypoint"]["format"], "module:function")

    def test_identity_provider_is_replaceable(self):
        api = load_contract("api/contract.yaml")

        self.assertEqual(api["identity"]["integration"], "pluggable")
        self.assertEqual(api["identity"]["future_provider"], "identity_unit")
        self.assertIn(
            "Domain services MUST NOT depend directly on a specific authentication provider.",
            api["identity"]["rules"],
        )


if __name__ == "__main__":
    unittest.main()
