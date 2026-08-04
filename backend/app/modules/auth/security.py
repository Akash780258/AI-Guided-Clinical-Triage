"""
Authentication Security

Provides:
- Password hashing
- Password verification
- JWT Access Token
- JWT Refresh Token
- JWT Decoding
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ==========================================================
# Password Hashing
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# ==========================================================
# JWT Configuration
# ==========================================================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


# ==========================================================
# Password Utilities
# ==========================================================

def hash_password(password: str) -> str:
    """
    Hash a plaintext password.
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify plaintext password against hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# ==========================================================
# JWT Helpers
# ==========================================================

def _build_payload(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Internal helper to build JWT payload.
    """

    expire = datetime.now(timezone.utc) + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if additional_claims:
        payload.update(additional_claims)

    return payload


# ==========================================================
# Access Token
# ==========================================================

def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create JWT Access Token.
    """

    payload = _build_payload(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        additional_claims=additional_claims,
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ==========================================================
# Refresh Token
# ==========================================================

def create_refresh_token(
    subject: str,
) -> str:
    """
    Create JWT Refresh Token.
    """

    payload = _build_payload(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ==========================================================
# Decode Token
# ==========================================================

def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode JWT.

    Raises:
        JWTError
    """

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )


# ==========================================================
# Helpers
# ==========================================================

def get_subject(token: str) -> str:
    """
    Extract user id from token.
    """

    payload = decode_token(token)

    return str(payload["sub"])


def get_token_type(token: str) -> str:
    """
    Extract token type.
    """

    payload = decode_token(token)

    return str(payload["type"])


def is_access_token(token: str) -> bool:
    """
    Check if token is an access token.
    """

    try:
        return get_token_type(token) == "access"
    except JWTError:
        return False


def is_refresh_token(token: str) -> bool:
    """
    Check if token is a refresh token.
    """

    try:
        return get_token_type(token) == "refresh"
    except JWTError:
        return False