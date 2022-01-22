"""zhaws server websocket package."""
from zhaws.backports.enum import StrEnum


class ServerEvents(StrEnum):
    """Events that can be emitted by the server."""

    SHUTDOWN = "server_shutdown"
