import datetime
import json
import logging
import typing as t


class JSONFormatter(logging.Formatter):
    """
    Render logs as JSON.

    To add details to a log record, store them in a ``event_data``
    custom attribute. This dict is merged into the event.
    """

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        pass  # override logging.Formatter constructor

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": self.get_timestamp(record.created),
            "message": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
        }
        event_data = getattr(record, "event_data", None)
        if event_data:
            event.update(event_data)
        if record.exc_info:
            event["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            event["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(event)

    def get_timestamp(self, created: float) -> str:
        return datetime.datetime.utcfromtimestamp(created).isoformat()


class LoggerAdapter(logging.LoggerAdapter):
    """Add connection ID and client IP address to websockets logs."""

    def process(self, msg: str, kwargs: t.MutableMapping[str, t.Any]) -> tuple:
        try:
            websocket = kwargs["extra"]["websocket"]
        except KeyError:
            return msg, kwargs
        # TODO: drop hasattr check once https://github.com/python-websockets/websockets/issues/1428 is fixed
        if hasattr(websocket, "request_headers"):
            kwargs["extra"]["event_data"] = {
                "connection_id": str(websocket.id),
                "remote_addr": websocket.request_headers.get("X-Forwarded-For"),
            }
        return msg, kwargs


def init() -> None:
    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # talkative modules:
    logging.getLogger("aiohttp_retry").setLevel(logging.INFO)
