"""WS api for the select platform entity."""
from typing import Any, Awaitable, Union

import voluptuous as vol

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType

ATTR_OPTION = "option"
COMMAND_SELECT_OPTION = "select_select_option"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        COMMAND_SELECT_OPTION,
        {
            vol.Required(ATTR_OPTION): Union[str, int],
        },
    )
)
async def select_option(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Select an option."""
    await execute_platform_entity_command(
        server, client, message, "async_select_option"
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, select_option)
