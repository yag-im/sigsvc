import typing as t

ERROR_REQUEST_VALIDATION = (1400, "request validation error")
ERROR_SESSIONS_QUOTA_LIMIT_EXCEEDED = (1429, "sessions quota limit exceeded for user")
ERROR_SESSIONSVC = (1409, "sessionsvc error")
ERROR_SESSIONSVC_SESSION_NOT_FOUND = (1404, "sessionsvc: session not found")
ERROR_SIGSVC_OP = (1409, "sigsvc operational error")
ERROR_UNKNOWN_PEER = (1404, "unknown peer")


class BizException(Exception):
    def __init__(self, code: int, message: t.Any) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class SigsvcOpException(BizException):
    def __init__(self, message: t.Optional[t.Any]) -> None:
        code = ERROR_SIGSVC_OP[0]
        message = message or ERROR_SIGSVC_OP[1]
        super().__init__(code, message)


class SessionsQuotaLimitExceededException(BizException):
    def __init__(self) -> None:
        code = ERROR_SESSIONS_QUOTA_LIMIT_EXCEEDED[0]
        message = ERROR_SESSIONS_QUOTA_LIMIT_EXCEEDED[1]
        super().__init__(code, message)


class UnknownPeerException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_UNKNOWN_PEER[0]
        message = message or ERROR_UNKNOWN_PEER[1]
        super().__init__(code, message)


class RequestValidationException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_REQUEST_VALIDATION[0]
        message = message or ERROR_REQUEST_VALIDATION[1]
        super().__init__(code, message)


class SessionSvcException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_SESSIONSVC[0]
        message = message or ERROR_SESSIONSVC[1]
        super().__init__(code, message)


class SessionNotFoundException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_SESSIONSVC_SESSION_NOT_FOUND[0]
        message = message or ERROR_SESSIONSVC_SESSION_NOT_FOUND[1]
        super().__init__(code, message)
