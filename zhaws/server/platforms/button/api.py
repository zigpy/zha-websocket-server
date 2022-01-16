"""WS API for the button platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

COMMAND_PRESS = "button_press"


@decorators.websocket_command(platform_entity_command_schema(COMMAND_PRESS))
@decorators.async_response
async def press(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the button."""
    await execute_platform_entity_command(server, client, message, "async_press")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, press)
