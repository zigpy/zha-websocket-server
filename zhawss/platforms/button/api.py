"""WS API for the button platform entity."""
from typing import Any, Awaitable

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType

COMMAND_PRESS = "button_press"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(COMMAND_PRESS))
async def press(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the button."""
    await execute_platform_entity_command(server, client, message, "async_press")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, press)
