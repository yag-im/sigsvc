import asyncio
import logging as log
import os
import typing as t

import websockets
from websockets.legacy.server import HTTPResponse

from sigsvc.auth.handle import auth
from sigsvc.biz.log import LoggerAdapter
from sigsvc.biz.log import init as log_init
from sigsvc.biz.webrtc import handler as webrtc_handler

LISTEN_IP = os.environ.get("LISTEN_IP")
LISTEN_PORT = os.environ.get("LISTEN_PORT")


async def process_request(path: str, request_headers: websockets.Headers) -> t.Optional[HTTPResponse]:
    """Called during initial handshake.

    Yields `None` upon successful processing, or else provides an `HTTPResponse` (with an error code) to interrupt the
    initial handshake.
    """
    log.debug(f"request path: {path}")  # pylint: disable=logging-fstring-interpolation
    return await auth(request_headers)


async def main() -> None:
    async with websockets.serve(
        webrtc_handler,
        host=LISTEN_IP,
        port=LISTEN_PORT,
        process_request=process_request,
        logger=LoggerAdapter(log.getLogger("websockets.server"), None),
    ):
        await asyncio.Future()


if __name__ == "__main__":
    log_init()
    asyncio.run(main())
