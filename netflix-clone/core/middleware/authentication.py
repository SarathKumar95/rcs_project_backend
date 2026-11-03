import hmac
import os
from typing import Iterable, Optional, Set, Tuple

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from core.auth.identity import AuthenticatedUser, UserRole


MAX_USER_ID_LENGTH = 10
MAX_USER_ID = 2_147_483_647


class AuthenticationMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        excluded_routes: Optional[Iterable[Tuple[str, str]]] = None,
        gateway_secret: Optional[str] = None,
    ) -> None:
        self.app = app
        self.excluded_routes: Set[Tuple[str, str]] = {
            (path, method.upper()) for path, method in (excluded_routes or ())
        }
        self.gateway_secret = (
            gateway_secret
            if gateway_secret is not None
            else os.getenv("GATEWAY_AUTH_SECRET")
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        route = (request.url.path, request.method.upper())
        if request.method == "OPTIONS" or route in self.excluded_routes:
            await self.app(scope, receive, send)
            return

        if not self.gateway_secret:
            response = JSONResponse(
                {"detail": "Gateway authentication is not configured"},
                status_code=503,
            )
            await response(scope, receive, send)
            return

        gateway_auth = request.headers.get("x-gateway-auth")
        if gateway_auth is None or not hmac.compare_digest(
            gateway_auth, self.gateway_secret
        ):
            await self._unauthorized(scope, receive, send)
            return

        raw_user_id = request.headers.get("x-verified-user-id")
        role = request.headers.get("x-verified-user-role")
        if (
            raw_user_id is None
            or len(raw_user_id) > MAX_USER_ID_LENGTH
            or not raw_user_id.isascii()
            or not raw_user_id.isdecimal()
        ):
            await self._unauthorized(scope, receive, send)
            return

        try:
            user_id = int(raw_user_id)
        except (ValueError, OverflowError):
            await self._unauthorized(scope, receive, send)
            return

        if user_id <= 0 or user_id > MAX_USER_ID:
            await self._unauthorized(scope, receive, send)
            return

        if role == "user":
            user_role: UserRole = "user"
        elif role == "admin":
            user_role = "admin"
        else:
            await self._unauthorized(scope, receive, send)
            return

        user = AuthenticatedUser(id=user_id, role=user_role)
        scope.setdefault("state", {})["user"] = user
        await self.app(scope, receive, send)

    @staticmethod
    async def _unauthorized(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            {"detail": "Authentication required"},
            status_code=401,
        )
        await response(scope, receive, send)
