"""WS api for the select platform entity."""
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

ATTR_OPTION = "option"
COMMAND_SELECT_OPTION = "select_select_option"


@decorators.websocket_command(
    platform_entity_command_schema(
        COMMAND_SELECT_OPTION,
        {
            vol.Required(ATTR_OPTION): str,
        },
    )
)
@decorators.async_response
async def select_option(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Select an option."""
    await execute_platform_entity_command(
        server, client, message, "async_select_option"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, select_option)
