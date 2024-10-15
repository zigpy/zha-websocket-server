"""Platform module for zhawss."""

from __future__ import annotations

from typing import Union

from zigpy.types.named import EUI64

from zha.application.platforms import Platform
from zhaws.server.websocket.api.model import WebSocketCommand


class PlatformEntityCommand(WebSocketCommand):
    """Base class for platform entity commands."""

    ieee: Union[EUI64, None]
    group_id: Union[int, None] = None
    unique_id: str
    platform: Platform
