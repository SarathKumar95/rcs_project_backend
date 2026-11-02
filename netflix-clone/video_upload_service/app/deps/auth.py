import hmac
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    role: str


def require_authenticated_user(
    user_id: Optional[str] = Header(default=None, alias="X-Verified-User-Id"),
    role: Optional[str] = Header(default=None, alias="X-Verified-User-Role"),
    gateway_auth: Optional[str] = Header(default=None, alias="X-Gateway-Auth"),
) -> AuthenticatedUser:
    expected_gateway_auth = os.getenv("GATEWAY_AUTH_SECRET")
    if not expected_gateway_auth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway authentication is not configured",
        )

    if gateway_auth is None or not hmac.compare_digest(
        gateway_auth, expected_gateway_auth
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        authenticated_user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if authenticated_user_id <= 0 or role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return AuthenticatedUser(id=authenticated_user_id, role=role)


def require_admin(
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
