"""Non-executing validation for submitted Python ZIP source bundles."""

import hashlib
import math
import re
import stat
import zipfile
import zlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath, PureWindowsPath

from .errors import SourceValidationError


_ENTRYPOINT_RE = re.compile(
    r"^(?P<module>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)"
    r":(?P<function>[A-Za-z_]\w*)$"
)


@dataclass(frozen=True)
class ArchiveLimits:
    max_archive_bytes: int = 20 * 1024 * 1024
    max_expanded_bytes: int = 100 * 1024 * 1024
    max_entries: int = 2_000
    max_compression_ratio: float = 100.0

    def __post_init__(self):
        for name in (
            "max_archive_bytes",
            "max_expanded_bytes",
            "max_entries",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

        ratio = self.max_compression_ratio
        if (
            isinstance(ratio, bool)
            or not isinstance(ratio, (int, float))
            or not math.isfinite(ratio)
            or ratio <= 0
        ):
            raise ValueError("max_compression_ratio must be a positive finite number")


@dataclass(frozen=True)
class ArchiveInspection:
    source_hash: str
    archive_size: int
    entry_count: int
    expanded_size: int
    python_files: tuple[str, ...]
    entrypoint: str


def _validate_member_path(name):
    if not name or "\x00" in name or "\\" in name:
        raise SourceValidationError("Archive contains an invalid path")

    if name.startswith("/") or PureWindowsPath(name).drive:
        raise SourceValidationError("Absolute paths are not allowed")

    parts = name.rstrip("/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SourceValidationError("Archive contains an unsafe path")

    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise SourceValidationError("Archive contains an unsafe path")

    return name.rstrip("/")


def inspect_source_archive(data, entrypoint, limits=None):
    """Inspect a ZIP in memory without extracting or executing its contents."""
    if not isinstance(data, bytes):
        raise TypeError("source archive must be bytes")

    if limits is None:
        limits = ArchiveLimits()
    elif not isinstance(limits, ArchiveLimits):
        raise TypeError("limits must be an ArchiveLimits instance")

    if not data:
        raise SourceValidationError("Source archive is empty")

    if len(data) > limits.max_archive_bytes:
        raise SourceValidationError("Source archive exceeds configured size limit")

    if not isinstance(entrypoint, str):
        raise SourceValidationError("Entrypoint must be a string")

    match = _ENTRYPOINT_RE.fullmatch(entrypoint)
    if not match:
        raise SourceValidationError(
            "Entrypoint must use module:function syntax"
        )

    try:
        archive = zipfile.ZipFile(BytesIO(data), mode="r")
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise SourceValidationError("Source is not a valid ZIP archive") from exc

    with archive:
        entries = archive.infolist()
        if not entries:
            raise SourceValidationError("ZIP archive contains no entries")
        if len(entries) > limits.max_entries:
            raise SourceValidationError("ZIP archive has too many entries")

        seen_paths = set()
        python_files = []
        expanded_size = 0

        for info in entries:
            path = _validate_member_path(info.filename)

            if path in seen_paths:
                raise SourceValidationError(
                    "ZIP archive contains duplicate paths"
                )
            seen_paths.add(path)

            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise SourceValidationError(
                    "Symbolic links are not allowed in source archives"
                )

            if info.flag_bits & 0x1:
                raise SourceValidationError(
                    "Encrypted ZIP entries are not supported"
                )

            if info.file_size < 0 or info.compress_size < 0:
                raise SourceValidationError("ZIP entry has invalid size metadata")

            if not info.is_dir():
                expanded_size += info.file_size

                if expanded_size > limits.max_expanded_bytes:
                    raise SourceValidationError(
                        "Expanded ZIP size exceeds configured limit"
                    )

                if info.file_size:
                    if info.compress_size == 0:
                        raise SourceValidationError(
                            "ZIP entry has an invalid compression ratio"
                        )
                    ratio = info.file_size / info.compress_size
                    if ratio > limits.max_compression_ratio:
                        raise SourceValidationError(
                            "ZIP entry exceeds compression ratio limit"
                        )

                if path.endswith(".py"):
                    python_files.append(path)

        module_path = match.group("module").replace(".", "/")
        possible_entrypoints = {
            f"{module_path}.py",
            f"{module_path}/__init__.py",
        }
        if not possible_entrypoints.intersection(seen_paths):
            raise SourceValidationError(
                "Declared entrypoint module was not found in the ZIP archive"
            )

        if not python_files:
            raise SourceValidationError(
                "ZIP archive does not contain a Python source file"
            )

        # Read every member to detect corrupt compressed data. Nothing is
        # extracted to disk, and no source code is imported or executed.
        try:
            for info in entries:
                if not info.is_dir():
                    with archive.open(info, "r") as member:
                        while member.read(64 * 1024):
                            pass
        except (
            zipfile.BadZipFile,
            RuntimeError,
            OSError,
            EOFError,
            zlib.error,
        ) as exc:
            raise SourceValidationError(
                "ZIP archive contains unreadable or corrupted content"
            ) from exc

    return ArchiveInspection(
        source_hash=hashlib.sha256(data).hexdigest(),
        archive_size=len(data),
        entry_count=len(entries),
        expanded_size=expanded_size,
        python_files=tuple(sorted(python_files)),
        entrypoint=entrypoint,
    )
