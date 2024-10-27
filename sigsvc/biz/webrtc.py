import asyncio
import json
import logging as log
import typing as t

from websockets import ConnectionClosedError
from websockets.legacy.server import WebSocketServerProtocol

from sigsvc.biz.dto import (
    CreateSessionRequestDTO,
    CreateSessionResponseDTO,
    EndSessionRequestDTO,
    EndSessionResponseDTO,
    ErrorResponseDTO,
    GetSessionRequestDTO,
    GetSessionResponseDTO,
    GetSessionsResponseDTO,
    ListResponseDTO,
    PeerStatusResponseDTO,
    RequestType,
    SessionStartedRequestDTO,
    SetPeerStatusRequestDTO,
    StartSessionRequestDTO,
    SubmitWebRtcStatsRequestDTO,
    WelcomeResponseDTO,
)
from sigsvc.biz.errors import (
    BizException,
    RequestValidationException,
    UnknownPeerException,
)
from sigsvc.biz.peer import (
    Peer,
    PeerRole,
)
from sigsvc.biz.sessions_manager import SessionsManager
from sigsvc.services.sessionsvc import SessionSvcException

# pylint: disable=logging-fstring-interpolation


peers: t.Dict[str, Peer] = {}

consumers_to_producers_map: t.Dict[str, str] = {}

sessions_manager: SessionsManager = SessionsManager()


async def handle_connection_closed(peer: Peer) -> None:
    """
    The connection terminates under the following circumstances:
        - The producer closes the connection, usually when docker container exits due to:
            - Streamd exit: due to a crash or a scheduled shutdown (by inactivity timeout);
            - App exit: due to a crash or using a native exit option from the game menu;
        - The consumer closes the connection by:
            - Closing the browser tab: conn will be closed from the consumers' end, soft session close will occur;
            - Reloading the browser tab: conn will be closed from the producers' end, hard session close will occur;
            - Explicitly calling endSession (e.g. from the Exit Game dialog): conn will be closed from the producer ???
        - There is a networking issue with a producer or consumer.
    In each of these scenarios, we need to remove the relevant peer from the list of known peers and terminate all
    active sessions associated with that peer.
    """
    log.debug(f"handle_connection_closed - initiated by peer: {peer.id} (role: {peer.role})")
    if peer.id not in peers:
        # this is expected for cases when e.g. paused container resumes and old connection to it (with old peer_id)
        # is getting closed (this is raised from the container side on resume)
        # we should simply ignore this connection close event
        log.error(f"handle_connection_closed - unknown peer (from resumed container?): {peer.id}")
        return
    del peers[peer.id]
    peer_sessions = await sessions_manager.get_peer_sessions(peer)
    for session in peer_sessions:
        # only sessions closed by consumer should be paused: perform "soft" end_session (aka pause);
        # if producer closes the session, then container doesn't exist anymore: perform "hard" end_session (aka close)
        await handle_end_session(peer, EndSessionRequestDTO(sessionId=session.id, soft=peer.role == PeerRole.CONSUMER))


async def handle_end_session(peer: Peer, req: EndSessionRequestDTO) -> None:
    """
    The consumer has the ability to end the session by explicitly terminating the stream from the user interface (UI).
    Also called in case of a connection close (see handle_connection_closed).
    """
    log.debug(f"handle_end_session - peer: {peer.id} (role: {peer.role})")
    direct = True
    if peer.id not in peers:
        # indirect call (e.g. from the handle_connection_closed handler)
        log.debug("indirect end session call")
        direct = False
    else:
        # direct call (e.g. by consumer from the UAs' "Exit Game" dialog)
        log.debug("direct end session call")
    try:
        session = await sessions_manager.get_session(req.sessionId)
        if not session or session.ending:
            # someone else (most probably the other peer) has ended or is currenlty "ending" the session
            log.info("hope session will be terminated properly")
            if direct and peer.role == PeerRole.CONSUMER:
                # only consumers explicitly calling endSession know how to handle sessionEnded events
                await peer.send(EndSessionResponseDTO.Schema().dumps(EndSessionResponseDTO(session_id=req.sessionId)))
            return
        sessions_manager.set_session_ending(req.sessionId)
        other_peer_id = session.other_peer_id(peer.id)
        # this will raise invalid peer_id exception when e.g. new peer is trying to stop orphaned session between two
        # other peers
        if other_peer_id:
            other_peer = peers.get(other_peer_id, None)
            if other_peer:
                await other_peer.send(EndSessionRequestDTO.Schema().dumps(req))
                del peers[other_peer_id]
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error(f"handle_end_session error: {e}")
    if not session:
        return
    # so there is a session, but we've crashed in the try/catch block above
    if req.soft:
        log.debug(f"pausing session: {session.id}")
        await sessions_manager.pause_session(session_id=session.id)
    else:
        log.debug(f"closing session: {session.id}")
        await sessions_manager.close_session(session_id=session.id)
    if direct and peer.role == PeerRole.CONSUMER:
        # only consumers know how to handle sessionEnded events
        await peer.send(EndSessionResponseDTO.Schema().dumps(EndSessionResponseDTO(session_id=session.id)))


async def handle_peer_msg(peer: Peer, req: dict) -> None:
    log.debug(f"handle_peer_msg - peer: {peer.id}")
    try:
        session = await sessions_manager.get_session(req["sessionId"])
        if not session:
            log.error("handle_peer_msg: session %s not found", req["sessionId"])
            return
    except SessionSvcException as e:
        log.error(f"handle_peer_msg: {e}")
        return
    other_peer_id = session.other_peer_id(peer.id)
    if other_peer_id:
        other_peer = peers.get(other_peer_id, None)
        if other_peer:
            await other_peer.send(json.dumps(req))


async def handle_start_session(session_id: str, peer_producer_id: str, peer_consumer: Peer) -> None:
    log.debug(
        f"handle_start_session - session_id: {session_id}, producer: {peer_producer_id}, consumer: {peer_consumer.id}"
    )
    peer_producer = peers.get(peer_producer_id, None)
    if not peer_producer:
        raise UnknownPeerException(f"producer peer (id: {peer_producer_id}) is unknown")
    await sessions_manager.start_session(session_id, peer_consumer.ws_conn_id, peer_producer.id, peer_consumer.id)
    await peer_producer.send(
        StartSessionRequestDTO.Schema().dumps(StartSessionRequestDTO(peerId=peer_consumer.id, sessionId=session_id))
    )
    await peer_consumer.send(
        SessionStartedRequestDTO.Schema().dumps(SessionStartedRequestDTO(peerId=peer_producer.id, sessionId=session_id))
    )


async def handle_list(peer: Peer) -> None:
    """Handles a list request for a consumer."""
    log.debug(f"handle_list - peer: {peer.id}")
    if peer.id in consumers_to_producers_map:
        producer_id = consumers_to_producers_map[peer.id]
        if producer_id in peers:
            await peer.send(
                ListResponseDTO.Schema().dumps(
                    ListResponseDTO(producers=[ListResponseDTO.Producer(id=producer_id, meta=peers[producer_id].meta)])
                )
            )
        return
    await peer.send(ListResponseDTO.Schema().dumps(ListResponseDTO(producers=[])))


async def handle_set_peer_status(peer: Peer, req: SetPeerStatusRequestDTO) -> None:
    log.debug(f"handle_set_peer_status - peer: {peer.id}")
    peer.meta = req.meta
    res = PeerStatusResponseDTO.Schema().dumps(
        PeerStatusResponseDTO(
            roles=req.roles,
            meta=peer.meta,
            peerId=peer.id,
        )
    )
    if "listener" in req.roles:
        peer.role = PeerRole.CONSUMER
    elif "producer" in req.roles:
        peer.role = PeerRole.PRODUCER
        # producer (peer.id) has joined and prepared a stream for consumerId
        # if consumer has not yet connected, it will obtain a producer reference in a list() call response later
        if peer.meta and "consumerId" in peer.meta:
            consumer_id = peer.meta["consumerId"]
            consumers_to_producers_map[consumer_id] = peer.id
            if consumer_id in peers:
                await peers[consumer_id].send(res)
    else:
        raise RequestValidationException(f"unknown peer role: {req.roles}")
    # we always need to send a confirmation to the original peer as well
    await peer.send(res)


async def handle_create_session(peer: Peer, req: CreateSessionRequestDTO) -> None:
    res = await sessions_manager.create_session(peer, req)
    await peer.send(CreateSessionResponseDTO.Schema().dumps(CreateSessionResponseDTO(session_id=res.session_id)))


async def handle_get_session(peer: Peer, req: GetSessionRequestDTO) -> None:
    res = await sessions_manager.get_session(req.sessionId)
    if res:
        await peer.send(GetSessionResponseDTO.Schema().dumps(GetSessionResponseDTO(res)))
    else:
        await peer.send("{}")


async def handle_get_sessions(peer: Peer) -> None:
    res = []

    if peer.role == PeerRole.CONSUMER:
        res = await sessions_manager.get_user_sessions(peer.user_id)  # type: ignore
    elif peer.role == PeerRole.PRODUCER:
        res = await sessions_manager.get_producer_sessions(peer.id)
    else:
        raise RequestValidationException(f"unknown peer role: {peer.role}")
    await peer.send(GetSessionsResponseDTO.Schema().dumps(GetSessionsResponseDTO(sessions=res)))


async def handle_submit_webrtc_stats(req: SubmitWebRtcStatsRequestDTO) -> None:
    await sessions_manager.submit_webrtc_stats(req.sessionId, req.stats)


async def handler(websocket: WebSocketServerProtocol) -> None:
    """Main webrtc signaling handler."""
    peer = Peer.from_ws(websocket)
    peers[peer.id] = peer

    # `connection closed` handler setup
    closed = asyncio.ensure_future(websocket.wait_closed())
    closed.add_done_callback(lambda task: asyncio.create_task(handle_connection_closed(peer)))

    await peer.send(WelcomeResponseDTO.Schema().dumps(WelcomeResponseDTO(peerId=peer.id)))

    async for msg in peer.ws:
        try:
            msg = json.loads(msg)
            if msg["type"] == RequestType.SET_PEER_STATUS.value:
                await handle_set_peer_status(peer, SetPeerStatusRequestDTO.Schema().load(data=msg))
            elif msg["type"] == RequestType.LIST.value:
                await handle_list(peer)
            elif msg["type"] == RequestType.CREATE_SESSION.value:
                await handle_create_session(peer, CreateSessionRequestDTO.Schema().load(data=msg))
            elif msg["type"] == RequestType.START_SESSION.value:
                req_start_session: StartSessionRequestDTO = StartSessionRequestDTO.Schema().load(data=msg)
                await handle_start_session(
                    session_id=req_start_session.sessionId,
                    peer_producer_id=req_start_session.peerId,
                    peer_consumer=peer,
                )
            elif msg["type"] == RequestType.PEER.value:
                # TODO: peer request contains dynamic attributes, so handling it as a dict.
                # Change it to the dataclass DTO.
                await handle_peer_msg(peer, msg)
            elif msg["type"] == RequestType.END_SESSION.value:
                await handle_end_session(peer, EndSessionRequestDTO.Schema().load(data=msg))
            elif msg["type"] == RequestType.GET_SESSIONS.value:
                await handle_get_sessions(peer)
            elif msg["type"] == RequestType.GET_SESSION.value:
                await handle_get_session(peer, GetSessionRequestDTO.Schema().load(data=msg))
            elif msg["type"] == RequestType.SUBMIT_WEBRTC_STATS.value:
                await handle_submit_webrtc_stats(SubmitWebRtcStatsRequestDTO.Schema().load(data=msg))
            else:
                raise RequestValidationException(f"unknown request type: {msg}")
        except ConnectionClosedError as e:
            log.warning(f"connection closed error: {e}, peer_id: {peer.id}, connection_id: {peer.ws.id}")
            break
        except BizException as e:
            log.error(f"biz exception occured: {e}, peer_id: {peer.id}, connection_id: {peer.ws.id}")
            await peer.send(ErrorResponseDTO.Schema().dumps(ErrorResponseDTO(code=e.code, message=e.message)))
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(
                f"exception occured in the msg polling loop: {e}, peer_id: {peer.id}, connection_id: {peer.ws.id}"
            )
