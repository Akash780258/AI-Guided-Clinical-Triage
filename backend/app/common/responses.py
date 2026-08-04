"""
Standard API response models for AGCT.

Every API endpoint should return one of these response models to ensure
consistent response formatting across the application.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """
    Represents a single validation or business error.
    """

    field: str | None = None
    message: str


class ApiResponse(BaseModel, Generic[T]):
    """
    Generic success response.
    """

    model_config = ConfigDict(from_attributes=True)

    success: bool = True

    message: str = "Request completed successfully."

    data: T | None = None

    metadata: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """
    Generic error response.
    """

    success: bool = False

    message: str

    errors: list[ErrorDetail] = Field(default_factory=list)


class PaginatedResponse(ApiResponse[list[T]], Generic[T]):
    """
    Standard paginated response.
    """

    page: int

    page_size: int

    total_items: int

    total_pages: int