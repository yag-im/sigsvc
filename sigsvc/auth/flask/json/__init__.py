from __future__ import annotations

import json as _json
import typing as t

from .provider import _default


def dumps(obj: t.Any, **kwargs: t.Any) -> str:
    """Serialize data as JSON."""

    kwargs.setdefault("default", _default)
    return _json.dumps(obj, **kwargs)


def loads(s: str | bytes, **kwargs: t.Any) -> t.Any:
    """Deserialize data as JSON."""
    return _json.loads(s, **kwargs)
