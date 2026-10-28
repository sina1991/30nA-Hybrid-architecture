import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_manager.errors import SourceValidationError
from code_manager.source_archive import ArchiveLimits, inspect_source_archive


def make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class SourceArchiveTests(unittest.TestCase):
    def test_valid_archive_returns_exact_source_hash(self):
        source = "def run(payload):\n    return payload\n"
        data = make_zip({
            "sample/__init__.py": "",
            "sample/main.py": source,
        })
        result = inspect_source_archive(data, "sample.main:run")

        self.assertEqual(result.source_hash, hashlib.sha256(data).hexdigest())
        self.assertEqual(result.archive_size, len(data))
        self.assertIn("sample/main.py", result.python_files)

    def test_invalid_zip_is_rejected(self):
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(b"not a zip", "sample.main:run")

    def test_entrypoint_format_is_required(self):
        data = make_zip({"sample/main.py": "def run(): pass"})
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(data, "sample.main.run")

    def test_non_string_entrypoint_is_rejected(self):
        data = make_zip({"sample/main.py": "def run(): pass"})
        for entrypoint in (None, 123, [], {}):
            with self.subTest(entrypoint=entrypoint):
                with self.assertRaises(SourceValidationError):
                    inspect_source_archive(data, entrypoint)

    def test_invalid_limits_are_rejected(self):
        invalid_values = (
            {"max_archive_bytes": 0},
            {"max_expanded_bytes": -1},
            {"max_entries": 0},
            {"max_compression_ratio": 0},
            {"max_compression_ratio": float("inf")},
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    ArchiveLimits(**values)

    def test_wrong_limits_type_is_rejected(self):
        data = make_zip({"sample/main.py": "def run(): pass"})
        with self.assertRaises(TypeError):
            inspect_source_archive(data, "sample.main:run", limits={})

    def test_missing_entrypoint_module_is_rejected(self):
        data = make_zip({"other.py": "def run(): pass"})
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(data, "sample.main:run")

    def test_path_traversal_is_rejected(self):
        data = make_zip({
            "../outside.py": "def run(): pass",
            "sample/main.py": "def run(): pass",
        })
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(data, "sample.main:run")

    def test_archive_size_limit_is_enforced(self):
        data = make_zip({"sample/main.py": "def run(): pass"})
        limits = ArchiveLimits(max_archive_bytes=10)
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(data, "sample.main:run", limits)

    def test_entry_count_limit_is_enforced(self):
        data = make_zip({
            "sample/main.py": "def run(): pass",
            "sample/extra.py": "VALUE = 1",
        })
        limits = ArchiveLimits(max_entries=1)
        with self.assertRaises(SourceValidationError):
            inspect_source_archive(data, "sample.main:run", limits)

    def test_no_source_is_executed_during_inspection(self):
        data = make_zip({
            "sample/main.py": (
                "raise RuntimeError('must not execute during inspection')"
            ),
        })
        result = inspect_source_archive(data, "sample.main:run")
        self.assertEqual(result.entrypoint, "sample.main:run")


if __name__ == "__main__":
    unittest.main()
