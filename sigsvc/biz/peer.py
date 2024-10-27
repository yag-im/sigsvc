import logging as log
import typing as t
import uuid
from dataclasses import dataclass
from enum import Enum
from http.cookies import SimpleCookie

from websockets import WebSocketServerProtocol

from sigsvc.auth.handle import (
    FLASK_SESSION_COOKIE_NAME,
    get_user_id,
)
from sigsvc.biz.errors import RequestValidationException

WS_CONN_ID_COOKIE_NAME = "sigsvc_wsconnid"


class PeerRole(Enum):
    PRODUCER = 1
    CONSUMER = 2


@dataclass
class Peer:
    id: str
    ws: WebSocketServerProtocol
    ws_conn_id: str  # value comes from the cookie (sticky-session)
    user_id: t.Optional[int] = None  # value comes from the flask session cookie, only for consumer session (UA)
    role: t.Optional[PeerRole] = None
    meta: t.Optional[t.Dict] = None

    async def send(self, msg: str) -> None:
        log.info(f">>> {self.id} [{self.role}]: {msg}")  # pylint: disable=logging-fstring-interpolation
        await self.ws.send(msg)

    async def receive(self) -> str:
        msg = await self.ws.recv()
        log.info(f"<<< {self.id} [{self.role}]: {msg}")  # pylint: disable=logging-fstring-interpolation
        return msg

    async def close(self) -> None:
        await self.ws.close()

    @classmethod
    def from_ws(cls, websocket: WebSocketServerProtocol) -> t.Self:
        peer_id = str(uuid.uuid4())
        user_id = None
        ws_conn_id = None
        if "cookie" in websocket.request_headers:
            raw_cookie = websocket.request_headers["cookie"]
            cookie = SimpleCookie()
            cookie.load(raw_cookie)
            if WS_CONN_ID_COOKIE_NAME in cookie:
                ws_conn_id = cookie[WS_CONN_ID_COOKIE_NAME].value
            else:
                raise RequestValidationException(f"no {WS_CONN_ID_COOKIE_NAME} cookie found")
            if FLASK_SESSION_COOKIE_NAME in cookie:
                # this is a consumer (UA) connection, producer (streamd) uses auth token instead
                session_cookie = cookie[FLASK_SESSION_COOKIE_NAME].value
                user_id = get_user_id(session_cookie)
        else:
            raise RequestValidationException("no cookies found")
        # `role` and `meta`` will be set later through the setPeerStatus() call.
        return cls(ws=websocket, id=peer_id, ws_conn_id=ws_conn_id, user_id=user_id)
