import typing as t
from dataclasses import field
from enum import StrEnum

from marshmallow import Schema
from marshmallow_dataclass import dataclass

from sigsvc.biz.errors import UnknownPeerException
from sigsvc.services.dto.sessionsvc import SessionDC

# pylint: disable=invalid-name


@dataclass
class Session(SessionDC):
    ending: bool = False

    def other_peer_id(self, peer_id: str) -> t.Optional[str]:
        if peer_id == self.ws_conn.consumer_id:
            return self.ws_conn.producer_id
        elif peer_id == self.ws_conn.producer_id:
            return self.ws_conn.consumer_id
        else:
            raise UnknownPeerException(f"invalid peer_id: {peer_id}")

    @classmethod
    def from_sessiondc(cls, sessiondc: SessionDC) -> t.Self:
        # pylint: disable=unexpected-keyword-arg
        return cls(
            id=sessiondc.id,
            app_release_uuid=sessiondc.app_release_uuid,
            container=sessiondc.container,
            status=sessiondc.status,
            updated=sessiondc.updated,
            user_id=sessiondc.user_id,
            ws_conn=sessiondc.ws_conn,
        )


class RequestType(StrEnum):
    UNKNOWN = "unknown"
    SET_PEER_STATUS = "setPeerStatus"
    LIST = "list"
    CREATE_SESSION = "createSession"
    START_SESSION = "startSession"
    SESSION_STARTED = "sessionStarted"
    PEER = "peer"
    END_SESSION = "endSession"
    GET_SESSIONS = "getSessions"
    GET_SESSION = "getSession"
    SUBMIT_WEBRTC_STATS = "submitWebRtcStats"


@dataclass
class BaseRequestDTO:
    type: RequestType = field(default=RequestType.UNKNOWN, metadata={"by_value": True}, kw_only=True)


@dataclass
class SetPeerStatusRequestDTO(BaseRequestDTO):
    meta: dict
    roles: list[str]  # TODO: PeerRole enum
    peerId: t.Optional[str] = None  # TODO: check why only producer sends this value and if we need it
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class CreateSessionRequestDTO(BaseRequestDTO):
    app_release_uuid: str
    preferred_dcs: t.Optional[list[str]] = field(default=None)
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class ListRequestDTO(BaseRequestDTO):
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class StartSessionRequestDTO(BaseRequestDTO):
    def __post_init__(self) -> None:
        self.type = RequestType.START_SESSION

    peerId: str
    sessionId: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class SessionStartedRequestDTO(BaseRequestDTO):
    def __post_init__(self) -> None:
        self.type = RequestType.SESSION_STARTED

    peerId: str
    sessionId: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class EndSessionRequestDTO(BaseRequestDTO):
    """Stop and close session.

    Either comes from UA or sent by sigsvc to the participating peers. __post_init__() is used in the latter case.
    """

    def __post_init__(self) -> None:
        self.type = RequestType.END_SESSION

    sessionId: str
    soft: bool = False
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class PeerRequestDTO(BaseRequestDTO):
    """Various peer messages for WebRTC session establishement."""

    sessionId: str
    # TODO: various dynamic fields depending on the message, need to create separate peer requests classes
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class GetSessionsRequestDTO(BaseRequestDTO):
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class GetSessionRequestDTO(BaseRequestDTO):
    def __post_init__(self) -> None:
        self.type = RequestType.GET_SESSION

    sessionId: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class SubmitWebRtcStatsRequestDTO(BaseRequestDTO):
    def __post_init__(self) -> None:
        self.type = RequestType.SUBMIT_WEBRTC_STATS

    sessionId: str
    stats: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


# we call "responses" messages which are sent back to the original requester peer
class ResponseType(StrEnum):
    UNKNOWN = "unknown"
    LIST = "list"
    PEER_STATUS = "peerStatusChanged"
    SESSION_CREATED = "sessionCreated"
    WELCOME = "welcome"
    ERROR = "error"
    SESSIONS_LIST = "sessionsList"
    SESSION = "session"
    SESSION_ENDED = "sessionEnded"


@dataclass
class BaseResponseDTO:
    type: ResponseType = field(default=ResponseType.UNKNOWN, metadata={"by_value": True}, kw_only=True)


@dataclass
class WelcomeResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.WELCOME

    peerId: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class PeerStatusResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.PEER_STATUS

    roles: list[str]
    meta: dict
    peerId: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class ListResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.LIST

    @dataclass
    class Producer:
        id: str
        meta: t.Optional[dict] = None

    producers: list[Producer]
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class CreateSessionResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.SESSION_CREATED

    session_id: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class EndSessionResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.SESSION_ENDED

    session_id: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class ErrorResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.ERROR

    code: int
    message: str
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class GetSessionsResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.SESSIONS_LIST

    sessions: list[Session]
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name


@dataclass
class GetSessionResponseDTO(BaseResponseDTO):
    def __post_init__(self) -> None:
        self.type = ResponseType.SESSION

    session: Session
    Schema: t.ClassVar[t.Type[Schema]] = Schema  # pylint: disable=invalid-name
