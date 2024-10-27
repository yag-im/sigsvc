import hashlib
import http
import logging as log
import os
import typing as t
from http.cookies import SimpleCookie

from itsdangerous import (
    BadSignature,
    URLSafeTimedSerializer,
)
from websockets import Headers
from websockets.legacy.server import HTTPResponse

from sigsvc.auth.flask.json.tag import TaggedJSONSerializer

# pylint: disable=logging-fstring-interpolation
AUTH_TOKEN_COOKIE_NAME = "sigsvc_authtoken"  # nosec B105:hardcoded_password_string
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")  # SECRET_KEY
FLASK_SESSION_COOKIE_NAME = "session"  # SESSION_COOKIE_NAME
FLASK_SESSION_LIFETIME = int(os.environ.get("FLASK_PERMANENT_SESSION_LIFETIME", 2678400))  # PERMANENT_SESSION_LIFETIME
# values from https://github.com/pallets/flask/blob/708d62d7172a30c5b0ace1d212c5a3bc2b53b98c/src/flask/sessions.py#L277
FLASK_SIGN_SALT = "cookie-session"
FLASK_SIGN_KEY_DERIVATION = "hmac"
FLASK_SIGN_DIGEST_METHOD = staticmethod(hashlib.sha1)

AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
DEBUG_NO_AUTH = os.environ.get("DEBUG_NO_AUTH", "false").lower() == "true"


def get_flask_signing_serializer() -> URLSafeTimedSerializer:
    signer_kwargs = {"key_derivation": FLASK_SIGN_KEY_DERIVATION, "digest_method": FLASK_SIGN_DIGEST_METHOD}
    return URLSafeTimedSerializer(
        FLASK_SECRET_KEY,
        salt=FLASK_SIGN_SALT,
        serializer=TaggedJSONSerializer(),
        signer_kwargs=signer_kwargs,
    )


def get_user_id(session_cookie: str) -> int:
    s = get_flask_signing_serializer()
    data = s.loads(session_cookie, max_age=FLASK_SESSION_LIFETIME)
    return int(data["_user_id"])


async def auth(request_headers: Headers) -> t.Optional[HTTPResponse]:
    """
    Perform authentication and yield None upon successful authentication,
    or else provide an HTTPResponse (UNAUTHORIZED) to interrupt the initial handshake.
    """
    if DEBUG_NO_AUTH:
        return None
    if "cookie" in request_headers:
        raw_cookie = request_headers["cookie"]
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        if AUTH_TOKEN_COOKIE_NAME in cookie:
            auth_token = cookie[AUTH_TOKEN_COOKIE_NAME].value
            if auth_token == AUTH_TOKEN:
                log.debug("successfully authenticated service (streamd?)")
                return None
            else:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid auth token\n"
        elif FLASK_SESSION_COOKIE_NAME in cookie:
            session_cookie = cookie[FLASK_SESSION_COOKIE_NAME].value
            try:
                user_id = get_user_id(session_cookie)
                log.debug(f"successfully authenticated user (user_id: {user_id})")
                return None
            except BadSignature:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid auth token\n"
    return http.HTTPStatus.UNAUTHORIZED, [], b"Missing auth token\n"
