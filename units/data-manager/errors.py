class DataManagerError(Exception):
    code = "DATA_ERROR"
    status = 400
    retryable = False

    def __init__(self, message, context=None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class NotFound(DataManagerError):
    code = "NOT_FOUND"
    status = 404


class Conflict(DataManagerError):
    code = "CONFLICT"
    status = 409


class Forbidden(DataManagerError):
    code = "FORBIDDEN"
    status = 403


class InvalidInput(DataManagerError):
    code = "INVALID_INPUT"
    status = 400


class UnsupportedVersion(DataManagerError):
    code = "UNSUPPORTED_VERSION"
    status = 400
