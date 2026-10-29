"""Runs inside the isolated worker container; not a security boundary by itself."""
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile


def _load_vendored_wheels(archive_path):
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            try:
                manifest_bytes = archive.read("vendor/dependencies.json")
            except KeyError:
                # Legacy/stdlib-only artifacts have no vendored dependency manifest.
                return []
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            if manifest.get("version") != 1 or not isinstance(manifest.get("wheels"), list):
                raise ValueError("invalid vendored dependency manifest")
            wheels = manifest["wheels"]
            if len(wheels) > 64:
                raise ValueError("too many vendored wheels")
            temp_root = Path(tempfile.mkdtemp(prefix="worker-vendor-", dir="/tmp"))
            temp_root.chmod(0o700)
            paths = []
            total_size = 0
            seen = set()
            for item in wheels:
                if not isinstance(item, dict):
                    raise ValueError("invalid wheel manifest entry")
                filename = item.get("filename")
                digest = item.get("sha256")
                if (not isinstance(filename, str)
                        or re.fullmatch(r"[A-Za-z0-9_.+-]+-py3-none-any\.whl", filename) is None
                        or filename in seen
                        or not isinstance(digest, str)
                        or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
                    raise ValueError("invalid vendored wheel identity")
                seen.add(filename)
                member = "vendor/" + filename
                info = archive.getinfo(member)
                if info.file_size > 8 * 1024 * 1024:
                    raise ValueError("vendored wheel exceeds size limit")
                total_size += info.file_size
                if total_size > 8 * 1024 * 1024:
                    raise ValueError("vendored wheels exceed total size limit")
                data = archive.read(info)
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("vendored wheel SHA-256 mismatch")
                path = temp_root / filename
                path.write_bytes(data)
                path.chmod(0o600)
                paths.append(str(path))
            return paths
    except zipfile.BadZipFile as exc:
        raise ValueError("invalid built artifact ZIP") from exc


def main():
    archive, entrypoint = sys.argv[1:3]
    sys.path.insert(0, archive)
    data = json.load(sys.stdin)
    try:
        wheels = _load_vendored_wheels(archive)
        for path in reversed(wheels):
            sys.path.insert(1, path)
        module, function = entrypoint.split(':', 1)
        result = getattr(importlib.import_module(module), function)(data['input'], data['configuration'])
        print(json.dumps({'ok': True, 'result': result}, allow_nan=False))
    except BaseException as exc:
        print(json.dumps({'ok': False, 'error': {'code': 'EXECUTION_ERROR', 'message': str(exc)[:512]}}))
if __name__ == '__main__':
    main()
