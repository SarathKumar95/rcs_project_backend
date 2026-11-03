import asyncio
import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.auth.dependencies import require_admin, require_authenticated_user
from core.auth.identity import AuthenticatedUser
from core.middleware.authentication import AuthenticationMiddleware


def make_scope(method="GET", path="/videos/", headers=()):
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": list(headers),
        "server": ("test", 80),
        "client": ("test", 1234),
    }


async def invoke_middleware(middleware, method="GET", path="/videos/", headers=()):
    received = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        received.append(message)

    await middleware(make_scope(method, path, headers), receive, send)
    start = next(message for message in received if message["type"] == "http.response.start")
    body = next(
        (message.get("body", b"") for message in received if message["type"] == "http.response.body"),
        b"",
    )
    return start["status"], json.loads(body) if body else None


class SharedAuthenticationMiddlewareTests(unittest.TestCase):
    def setUp(self):
        async def app(scope, receive, send):
            user = scope.get("state", {}).get("user")
            response = JSONResponse(
                {"user_id": user.id, "role": user.role} if user else {"user": None}
            )
            await response(scope, receive, send)

        self.app = app

    def test_missing_and_invalid_gateway_assertions_return_401(self):
        middleware = AuthenticationMiddleware(self.app, gateway_secret="secret")
        status, _ = asyncio.run(invoke_middleware(middleware))
        self.assertEqual(status, 401)

        headers = [
            (b"x-verified-user-id", b"8"),
            (b"x-verified-user-role", b"user"),
            (b"x-gateway-auth", b"incorrect"),
        ]
        status, _ = asyncio.run(invoke_middleware(middleware, headers=headers))
        self.assertEqual(status, 401)

    def test_missing_gateway_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            middleware = AuthenticationMiddleware(self.app)
            status, _ = asyncio.run(invoke_middleware(middleware))
        self.assertEqual(status, 503)

    def test_invalid_user_ids_and_roles_return_401(self):
        middleware = AuthenticationMiddleware(self.app, gateway_secret="secret")
        invalid_ids = ("0", "2147483648", "9" * 5000, "not-a-number")
        invalid_role = (
            (b"x-verified-user-id", b"8"),
            (b"x-verified-user-role", b"owner"),
            (b"x-gateway-auth", b"secret"),
        )
        for user_id in invalid_ids:
            headers = (
                (b"x-verified-user-id", user_id.encode("ascii")),
                (b"x-verified-user-role", b"admin"),
                (b"x-gateway-auth", b"secret"),
            )
            with self.subTest(user_id=user_id[:20]):
                status, _ = asyncio.run(invoke_middleware(middleware, headers=headers))
                self.assertEqual(status, 401)

        status, _ = asyncio.run(invoke_middleware(middleware, headers=invalid_role))
        self.assertEqual(status, 401)

    def test_valid_identity_is_stored_in_request_state(self):
        middleware = AuthenticationMiddleware(self.app, gateway_secret="secret")
        headers = (
            (b"x-verified-user-id", b"42"),
            (b"x-verified-user-role", b"admin"),
            (b"x-gateway-auth", b"secret"),
        )
        status, body = asyncio.run(invoke_middleware(middleware, headers=headers))
        self.assertEqual(status, 200)
        self.assertEqual(body, {"user_id": 42, "role": "admin"})

    def test_options_and_configured_route_exclusions_bypass_gateway_auth(self):
        middleware = AuthenticationMiddleware(
            self.app,
            excluded_routes={("/videos/internal/post-transcode-update", "POST")},
            gateway_secret="",
        )
        options_status, options_body = asyncio.run(
            invoke_middleware(middleware, method="OPTIONS")
        )
        callback_status, callback_body = asyncio.run(
            invoke_middleware(
                middleware,
                method="POST",
                path="/videos/internal/post-transcode-update",
            )
        )
        self.assertEqual((options_status, options_body), (200, {"user": None}))
        self.assertEqual((callback_status, callback_body), (200, {"user": None}))


class SharedAuthorizationDependencyTests(unittest.TestCase):
    def test_authenticated_user_dependency_reads_request_state(self):
        scope = make_scope()
        scope["state"] = {"user": AuthenticatedUser(id=12, role="user")}
        request = Request(scope)
        self.assertEqual(require_authenticated_user(request), AuthenticatedUser(12, "user"))

    def test_missing_state_identity_is_unauthorized(self):
        with self.assertRaises(HTTPException) as raised:
            require_authenticated_user(Request(make_scope()))
        self.assertEqual(raised.exception.status_code, 401)

    def test_user_is_forbidden_and_admin_is_allowed(self):
        with self.assertRaises(HTTPException) as raised:
            require_admin(AuthenticatedUser(id=12, role="user"))
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(
            require_admin(AuthenticatedUser(id=13, role="admin")),
            AuthenticatedUser(id=13, role="admin"),
        )


if __name__ == "__main__":
    unittest.main()
