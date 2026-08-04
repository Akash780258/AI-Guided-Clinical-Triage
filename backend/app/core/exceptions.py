"""
Global application exceptions for AGCT.

All business/domain exceptions should inherit from AppException.
The global exception handlers will convert these exceptions into
standardized API responses.
"""

from http import HTTPStatus
from typing import Any


class AppException(Exception):
    """
    Base exception for all AGCT business exceptions.
    """

    def __init__(
        self,
        *,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        error_code: str = "APP_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

        super().__init__(message)


# ==========================================================
# Authentication
# ==========================================================


class AuthenticationException(AppException):
    def __init__(
        self,
        message: str = "Authentication failed.",
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationException(AppException):
    def __init__(
        self,
        message: str = "Permission denied.",
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class InvalidCredentialsException(AuthenticationException):
    def __init__(self):
        super().__init__("Invalid email or password.")


class InvalidTokenException(AuthenticationException):
    def __init__(self):
        super().__init__("Invalid or expired token.")


class InactiveUserException(AuthenticationException):
    def __init__(self):
        super().__init__("User account is inactive.")


# ==========================================================
# Resources
# ==========================================================


class ResourceNotFoundException(AppException):
    def __init__(
        self,
        resource: str,
    ):
        super().__init__(
            message=f"{resource} not found.",
            status_code=HTTPStatus.NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(
        self,
        message: str,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.CONFLICT,
            error_code="RESOURCE_CONFLICT",
        )


class ValidationException(AppException):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


# ==========================================================
# AI / Clinical Modules
# ==========================================================


class AIServiceException(AppException):
    def __init__(
        self,
        message: str = "AI service unavailable.",
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error_code="AI_SERVICE_ERROR",
        )


class ExternalServiceException(AppException):
    def __init__(
        self,
        service: str,
    ):
        super().__init__(
            message=f"{service} is currently unavailable.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
        )