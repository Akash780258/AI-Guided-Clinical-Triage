"""
Authentication domain exceptions.

All authentication-related business exceptions should inherit from
AuthException so they can be handled globally by FastAPI.
"""


class AuthException(Exception):
    """
    Base class for all authentication exceptions.
    """

    default_message = "Authentication error."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidCredentialsError(AuthException):
    default_message = "Invalid email or password."


class UserAlreadyExistsError(AuthException):
    default_message = "A user with this email already exists."


class UserNotFoundError(AuthException):
    default_message = "User not found."


class InvalidTokenError(AuthException):
    default_message = "Invalid or expired token."


class InvalidTokenTypeError(AuthException):
    default_message = "Invalid token type."


class InactiveUserError(AuthException):
    default_message = "User account is inactive."


class EmailNotVerifiedError(AuthException):
    default_message = "Email address is not verified."


class PermissionDeniedError(AuthException):
    default_message = "Permission denied."