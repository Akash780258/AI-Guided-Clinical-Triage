"""
Authentication API

Provides endpoints for:

- Register
- Login
- Refresh Token
- Current User
- Change Password
- Verify Email
- Activate User
- Deactivate User
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth.dependencies import (
    get_auth_service,
    get_current_user,
)
from app.modules.auth.schemas import (
    MessageResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserPublic,
    UserRegister,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==========================================================
# Register
# ==========================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user.
    """

    user = await service.register(data)

    return UserResponse.model_validate(user)


# ==========================================================
# Login
# ==========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """
    Login user.
    """

    return await service.login(
        email=form_data.username,
        password=form_data.password,
    )


# ==========================================================
# Refresh Token
# ==========================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token.
    """

    return await service.refresh_access_token(request)


# ==========================================================
# Current User
# ==========================================================

@router.get(
    "/me",
    response_model=UserPublic,
)
async def me(
    current_user=Depends(get_current_user),
):
    """
    Get current authenticated user.
    """

    return UserPublic.model_validate(current_user)


# ==========================================================
# Change Password
# ==========================================================

@router.post(
    "/change-password",
    response_model=MessageResponse,
)
async def change_password(
    request: PasswordChangeRequest,
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Change password.
    """

    await service.change_password(
        user=current_user,
        request=request,
    )

    return MessageResponse(
        message="Password changed successfully."
    )


# ==========================================================
# Verify Email
# ==========================================================

@router.post(
    "/verify-email",
    response_model=UserResponse,
)
async def verify_email(
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Verify email.
    """

    user = await service.verify_email(current_user)

    return UserResponse.model_validate(user)


# ==========================================================
# Activate User
# ==========================================================

@router.post(
    "/activate",
    response_model=UserResponse,
)
async def activate_user(
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Activate current user.
    """

    user = await service.activate_user(current_user)

    return UserResponse.model_validate(user)


# ==========================================================
# Deactivate User
# ==========================================================

@router.post(
    "/deactivate",
    response_model=UserResponse,
)
async def deactivate_user(
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Deactivate current user.
    """

    user = await service.deactivate_user(current_user)

    return UserResponse.model_validate(user)