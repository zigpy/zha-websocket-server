"""WS api for the number platform entity."""
from typing import Any, Awaitable

import voluptuous as vol

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.types import ClientType, ServerType

ATTR_VALUE = "value"
COMMAND_SET_VALUE = "number_set_value"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        COMMAND_SET_VALUE,
        {
            vol.Required(ATTR_VALUE): vol.Coerce(float),
        },
    )
)
async def set_value(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Select an option."""
    await execute_platform_entity_command(server, client, message, "async_set_value")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, set_value)
