"""Stable domain exceptions for CODE MANAGER."""


class CodeManagerError(Exception):
    """Base exception for CODE MANAGER."""


class BlobIntegrityError(CodeManagerError):
    """A blob does not match its expected content digest."""


class SourceValidationError(CodeManagerError):
    """A source archive violates the source contract."""
