import typing as t
from enum import StrEnum

from sigsvc.biz.errors import UnknownPeerException
from sigsvc.services.dto.sessionsvc import (
    BaseDTO,
    SessionDC,
)


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


class BaseRequestDTO(BaseDTO):
    type: RequestType = RequestType.UNKNOWN


class SetPeerStatusRequestDTO(BaseRequestDTO):
    meta: dict
    roles: list[str]  # TODO: PeerRole enum
    peerId: t.Optional[str] = None  # TODO: check why only producer sends this value and if we need it


class CreateSessionRequestDTO(BaseRequestDTO):
    app_release_uuid: str
    preferred_dcs: t.Optional[list[str]] = None


class ListRequestDTO(BaseRequestDTO):
    pass


class StartSessionRequestDTO(BaseRequestDTO):
    type: RequestType = RequestType.START_SESSION
    peerId: str
    sessionId: str


class SessionStartedRequestDTO(BaseRequestDTO):
    type: RequestType = RequestType.SESSION_STARTED
    peerId: str
    sessionId: str


class EndSessionRequestDTO(BaseRequestDTO):
    """Stop and close session.

    Either comes from UA or sent by sigsvc to the participating peers.
    """

    type: RequestType = RequestType.END_SESSION
    sessionId: str
    soft: bool = False


class PeerRequestDTO(BaseRequestDTO):
    """Various peer messages for WebRTC session establishement."""

    sessionId: str
    # TODO: various dynamic fields depending on the message, need to create separate peer requests classes


class GetSessionsRequestDTO(BaseRequestDTO):
    pass


class GetSessionRequestDTO(BaseRequestDTO):
    type: RequestType = RequestType.GET_SESSION
    sessionId: str


class SubmitWebRtcStatsRequestDTO(BaseRequestDTO):
    type: RequestType = RequestType.SUBMIT_WEBRTC_STATS
    sessionId: str
    stats: str


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


class BaseResponseDTO(BaseDTO):
    type: ResponseType = ResponseType.UNKNOWN


class WelcomeResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.WELCOME
    peerId: str


class PeerStatusResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.PEER_STATUS
    roles: list[str]
    meta: dict
    peerId: str


class ListResponseDTO(BaseResponseDTO):
    class Producer(BaseDTO):
        id: str
        meta: t.Optional[dict] = None

    type: ResponseType = ResponseType.LIST
    producers: list[Producer]


class CreateSessionResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.SESSION_CREATED
    session_id: str


class EndSessionResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.SESSION_ENDED
    session_id: str


class ErrorResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.ERROR
    code: int
    message: str


class GetSessionsResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.SESSIONS_LIST
    sessions: list[Session]


class GetSessionResponseDTO(BaseResponseDTO):
    type: ResponseType = ResponseType.SESSION
    session: Session
