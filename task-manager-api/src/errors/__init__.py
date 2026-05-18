class AppError(Exception):
    code = "internal_error"
    http = 500

    def __init__(self, message="Internal error"):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    code = "validation_error"
    http = 400


class NotFoundError(AppError):
    code = "not_found"
    http = 404


class ConflictError(AppError):
    code = "conflict"
    http = 409


class AuthError(AppError):
    code = "auth_error"
    http = 401


class ForbiddenError(AppError):
    code = "forbidden"
    http = 403
