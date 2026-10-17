# sync with sessionsvc (sessionsvc/biz/dto.py)

import datetime
import typing as t
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class BaseDTO(BaseModel):
    # unknown fields are rejected (same as marshmallow's default `unknown=RAISE`)
    model_config = ConfigDict(extra="forbid")


class SessionStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class SessionDC(BaseDTO):
    class WsConn(BaseDTO):
        """Websocket connection parameters."""

        id: str  # unique ws connection id (used as a sticky session cookie value)
        consumer_id: str  # peer_id of the party awaiting for a stream (UA)
        producer_id: t.Optional[str] = None  # peer_id of the party producing a stream (streamd)

    class Container(BaseDTO):
        """Docker container parameters."""

        id: str
        node_id: str
        region: str
        cpuset_cpus: set[int]

    app_release_uuid: str
    container: t.Optional[Container] = None
    updated: datetime.datetime
    user_id: int
    ws_conn: WsConn
    id: str = ""
    status: t.Optional[SessionStatus] = None


class CreateSessionRequestDTO(BaseDTO):
    class WsConn(BaseDTO):
        """Websocket connection parameters."""

        id: str  # unique ws connection id (used as a sticky session cookie value)
        consumer_id: str  # peer_id of the party awaiting for a stream (UA)

    app_release_uuid: str
    user_id: int
    ws_conn: WsConn
    preferred_dcs: t.Optional[list[str]] = Field(default_factory=list)


class CreateSessionResponseDTO(BaseDTO):
    session_id: str


class StartSessionRequestDTO(BaseDTO):
    class WsConn(BaseDTO):
        id: str  # must be present for `resume` case
        consumer_id: str  # must be present for `resume` case
        producer_id: str

    ws_conn: WsConn


class GetSessionResponseDTO(BaseDTO):
    session: SessionDC


class GetSessionsResponseDTO(BaseDTO):
    sessions: list[SessionDC]


class SubmitWebRtcStatsRequestDTO(BaseDTO):
    stats: str  # json-encoded stats structure
