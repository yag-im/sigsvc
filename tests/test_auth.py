import http
import importlib
from unittest import mock

import pytest
from conf import (
    VALID_AUTH_TOKEN,
    VALID_FLASK_SESSION_COOKIE,
)
from websockets import Headers

import sigsvc.auth.handle as h


@pytest.mark.asyncio
class TestAuth:
    async def test_valid_auth_token(self):
        res = await h.auth(Headers({"cookie": f"auth-token={VALID_AUTH_TOKEN}"}))
        assert res is None

    async def test_valid_session_cookie(self):
        res = await h.auth(Headers({"cookie": f"session={VALID_FLASK_SESSION_COOKIE}"}))
        assert res is None

    async def test_invalid_auth_token(self):
        res = await h.auth(Headers({"cookie": "auth-token=dcba"}))
        assert res == (http.HTTPStatus.UNAUTHORIZED, [], b"Invalid auth token\n")

    async def test_invalid_session_cookie(self):
        res = await h.auth(Headers({"cookie": "session=.abc"}))
        assert res == (http.HTTPStatus.UNAUTHORIZED, [], b"Invalid auth token\n")

    async def test_no_auth_token_session_cookie(self):
        res = await h.auth(Headers({}))
        assert res == (http.HTTPStatus.UNAUTHORIZED, [], b"Missing auth token\n")

    @mock.patch.dict("os.environ", {"FLASK_PERMANENT_SESSION_LIFETIME": "1"})
    async def test_expired_session_cookie(self):
        importlib.reload(h)  # to re-apply os.environ
        res = await h.auth(Headers({"cookie": f"session={VALID_FLASK_SESSION_COOKIE}"}))
        assert res == (http.HTTPStatus.UNAUTHORIZED, [], b"Invalid auth token\n")
