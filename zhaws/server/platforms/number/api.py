"""WS api for the number platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

ATTR_VALUE = "value"
COMMAND_SET_VALUE = "number_set_value"


@decorators.websocket_command(
    platform_entity_command_schema(
        COMMAND_SET_VALUE,
        {
            vol.Required(ATTR_VALUE): vol.Coerce(float),
        },
    )
)
@decorators.async_response
async def set_value(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Select an option."""
    await execute_platform_entity_command(server, client, message, "async_set_value")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, set_value)
