import logging
import typing as t

import sigsvc.services.dto.sessionsvc as dto_sessionsvc
from sigsvc.biz.dto import (
    CreateSessionRequestDTO,
    Session,
)
from sigsvc.biz.errors import (
    SigsvcOpException,
    UnknownPeerException,
)
from sigsvc.biz.peer import (
    Peer,
    PeerRole,
)
from sigsvc.services import sessionsvc

log = logging.getLogger("sigsvc")


class SessionsManager:
    sessions_cache: t.Dict[str, Session] = {}

    def invalidate_cache(self, session_id: str) -> None:
        if session_id in self.sessions_cache:
            del self.sessions_cache[session_id]

    def set_session_ending(self, session_id: str) -> None:
        if session_id in self.sessions_cache:
            self.sessions_cache[session_id].ending = True
        else:
            log.error("set_session_ending: session %s not found", session_id)

    async def create_session(self, peer: Peer, req: CreateSessionRequestDTO) -> dto_sessionsvc.CreateSessionResponseDTO:
        """Runs a new app and creates a new session.

        If app already exist in a paused state - resume it with new ws_conn parameters.
        As a result, UI gets a message and puts app widget into the "ready to start [streaming] session" mode.
        """
        if peer.role != PeerRole.CONSUMER:
            raise SigsvcOpException("only consumers can run apps")
        if peer.user_id is None:
            raise SigsvcOpException("user_id is undefined")
        res: dto_sessionsvc.CreateSessionResponseDTO = await sessionsvc.create_session(
            dto_sessionsvc.CreateSessionRequestDTO(
                app_release_uuid=req.app_release_uuid,
                preferred_dcs=req.preferred_dcs,
                user_id=peer.user_id,
                ws_conn=dto_sessionsvc.CreateSessionRequestDTO.WsConn(id=peer.ws_conn_id, consumer_id=peer.id),
            )
        )
        return res

    async def start_session(self, session_id: str, ws_conn_id: str, producer_id: str, consumer_id: str) -> None:
        self.invalidate_cache(session_id)  # because session status has changes
        await sessionsvc.start_session(
            session_id,
            dto_sessionsvc.StartSessionRequestDTO(
                ws_conn=dto_sessionsvc.StartSessionRequestDTO.WsConn(
                    consumer_id=consumer_id, producer_id=producer_id, id=ws_conn_id
                )
            ),
        )
        await self.get_session(session_id)  # upd cache

    async def pause_session(self, session_id: str) -> None:
        await sessionsvc.pause_session(session_id)
        self.invalidate_cache(session_id)  # because session status has changes

    async def close_session(self, session_id: str) -> None:
        await sessionsvc.close_session(session_id)
        self.invalidate_cache(session_id)

    async def get_session(self, session_id: str) -> t.Optional[Session]:
        if session_id in self.sessions_cache:
            return self.sessions_cache[session_id]
        try:
            res = await sessionsvc.get_session(session_id)
        except sessionsvc.SessionNotFoundException:
            log.warning("session %s wasn't found", session_id)
            return None
        new_session = Session.from_sessiondc(res.session)
        # upd cache
        old_session = self.sessions_cache.get(session_id, None)
        if old_session:  # TODO: dirty patch
            new_session.ending = old_session.ending
        self.sessions_cache[session_id] = new_session
        return new_session

    async def get_user_sessions(self, user_id: int) -> list[Session]:
        res = await sessionsvc.get_user_sessions(user_id)
        return [Session.from_sessiondc(s) for s in res.sessions]

    async def get_consumer_sessions(self, consumer_id: str) -> list[Session]:
        res = await sessionsvc.get_consumer_sessions(consumer_id)
        return [Session.from_sessiondc(s) for s in res.sessions]

    async def get_producer_sessions(self, producer_id: str) -> list[Session]:
        res = await sessionsvc.get_producer_sessions(producer_id)
        return [Session.from_sessiondc(s) for s in res.sessions]

    async def get_peer_sessions(self, peer: Peer) -> list[Session]:
        if peer.role == PeerRole.CONSUMER:
            return await self.get_consumer_sessions(peer.id)
        elif peer.role == PeerRole.PRODUCER:
            return await self.get_producer_sessions(peer.id)
        else:
            raise UnknownPeerException(f"unknown peer role: {peer.role}")

    async def submit_webrtc_stats(self, session_id: str, stats: str) -> None:
        await sessionsvc.submit_webrtc_stats(session_id, dto_sessionsvc.SubmitWebRtcStatsRequestDTO(stats=stats))
