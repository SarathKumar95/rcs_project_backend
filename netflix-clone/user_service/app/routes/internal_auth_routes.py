from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.models.user import User
from app.utility.auth_utility import decode_access_token, extract_token_from_cookie


router = APIRouter()


@router.get("/check", include_in_schema=False)
async def check_authentication(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    token = extract_token_from_cookie(request)
    payload = decode_access_token(token)
    subject = payload.get("sub")

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
        )

    try:
        role = user.role_name
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not recognized",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "X-Verified-User-Id": str(user.id),
            "X-Verified-User-Role": role,
        },
    )
