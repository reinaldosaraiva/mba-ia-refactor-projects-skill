"""Domain exception hierarchy. The error handler middleware maps each to HTTP."""


class AppError(Exception):
    code = "internal_error"
    http = 500


class NotFoundError(AppError):
    code = "not_found"
    http = 404


class ValidationError(AppError):
    code = "validation_error"
    http = 400


class AuthError(AppError):
    code = "auth_error"
    http = 401


class ConflictError(AppError):
    code = "conflict"
    http = 409
