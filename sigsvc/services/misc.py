import typing as t
from types import TracebackType

from aiohttp_retry import (
    ExponentialRetry,
    RetryClient,
)

CONN_TIMEOUT = 3
READ_TIMEOUT = 10


async def get_http_client(read_timeout: int) -> RetryClient:
    retry_options = ExponentialRetry(attempts=0, start_timeout=3, exceptions={Exception}, retry_all_server_errors=False)
    client = RetryClient(
        raise_for_status=False,
        retry_options=retry_options,
        conn_timeout=CONN_TIMEOUT,
        read_timeout=read_timeout,
    )
    return client


class AsyncHttpClient:
    def __init__(self, read_timeout: int = READ_TIMEOUT) -> None:
        self.client = None
        self.read_timeout = read_timeout

    async def __aenter__(self) -> RetryClient:
        self.client = await get_http_client(self.read_timeout)
        return self.client

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_val: t.Optional[BaseException],
        exc_tb: t.Optional[TracebackType],
    ) -> None:
        if self.client:
            await self.client.close()
