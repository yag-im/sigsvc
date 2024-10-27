import logging
import os

from sigsvc.biz.errors import (
    SessionNotFoundException,
    SessionSvcException,
)
from sigsvc.services.dto.sessionsvc import (
    CreateSessionRequestDTO,
    CreateSessionResponseDTO,
    GetSessionResponseDTO,
    GetSessionsResponseDTO,
    StartSessionRequestDTO,
    SubmitWebRtcStatsRequestDTO,
)
from sigsvc.services.misc import AsyncHttpClient

SESSIONSVC_URL = os.environ["SESSIONSVC_URL"]

log = logging.getLogger("sigsvc.sessionsvc")


async def create_session(req: CreateSessionRequestDTO) -> CreateSessionResponseDTO:
    async with AsyncHttpClient(read_timeout=55) as client:
        try:
            async with client.post(
                url=f"{SESSIONSVC_URL}/sessions/create",
                json=CreateSessionRequestDTO.Schema().dump(req),
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
                return CreateSessionResponseDTO.Schema().load(data=await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def start_session(session_id: str, req: StartSessionRequestDTO) -> None:
    async with AsyncHttpClient() as client:
        try:
            async with client.post(
                url=f"{SESSIONSVC_URL}/sessions/{session_id}/start",
                json=StartSessionRequestDTO.Schema().dump(req),
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def pause_session(session_id: str) -> None:
    async with AsyncHttpClient() as client:
        try:
            async with client.post(
                url=f"{SESSIONSVC_URL}/sessions/{session_id}/pause",
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def close_session(session_id: str) -> None:
    async with AsyncHttpClient() as client:
        try:
            async with client.post(
                url=f"{SESSIONSVC_URL}/sessions/{session_id}/close",
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def get_session(session_id: str) -> GetSessionResponseDTO:
    async with AsyncHttpClient() as client:
        try:
            async with client.get(
                url=f"{SESSIONSVC_URL}/sessions/{session_id}",
            ) as res:
                res_json = await res.json()
                if res.status != 200:
                    if res.status == 409 and res_json["code"] == 1404:
                        raise SessionNotFoundException()
                    raise SessionSvcException(res_json)
                return GetSessionResponseDTO.Schema().load(data=res_json)
        except SessionSvcException as e:
            raise e
        except SessionNotFoundException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def get_user_sessions(user_id: int) -> GetSessionsResponseDTO:
    async with AsyncHttpClient() as client:
        try:
            async with client.get(
                url=f"{SESSIONSVC_URL}/users/{user_id}/sessions",
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
                return GetSessionsResponseDTO.Schema().load(data=await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def get_consumer_sessions(consumer_id: str) -> GetSessionsResponseDTO:
    async with AsyncHttpClient() as client:
        try:
            async with client.get(
                url=f"{SESSIONSVC_URL}/consumers/{consumer_id}/sessions",
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
                return GetSessionsResponseDTO.Schema().load(data=await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def get_producer_sessions(producer_id: str) -> GetSessionsResponseDTO:
    async with AsyncHttpClient() as client:
        try:
            async with client.get(
                url=f"{SESSIONSVC_URL}/producers/{producer_id}/sessions",
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
                return GetSessionsResponseDTO.Schema().load(data=await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e


async def submit_webrtc_stats(session_id: str, req: SubmitWebRtcStatsRequestDTO) -> None:
    async with AsyncHttpClient() as client:
        try:
            async with client.post(
                url=f"{SESSIONSVC_URL}/sessions/{session_id}/stats",
                json=SubmitWebRtcStatsRequestDTO.Schema().dump(req),
            ) as res:
                if res.status != 200:
                    raise SessionSvcException(await res.json())
        except SessionSvcException as e:
            raise e
        except Exception as e:
            log.exception(e)
            raise SessionSvcException from e
