from fastapi import Depends, HTTPException, Request, status

from core.auth.identity import AuthenticatedUser


def require_authenticated_user(request: Request) -> AuthenticatedUser:
    user = getattr(request.state, "user", None)
    if not isinstance(user, AuthenticatedUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def require_admin(
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
