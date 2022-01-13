"""WS API for the cover platform entity."""

# open, close, set position, stop


from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.platforms.cover import ATTR_POSITION
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class CoverCommands(StrEnum):
    """Cover commands."""

    OPEN = "cover_open"
    CLOSE = "cover_close"
    SET_POSITION = "cover_set_position"
    STOP = "cover_stop"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(CoverCommands.OPEN))
async def open(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Open the cover."""
    await execute_platform_entity_command(server, client, message, "async_open_cover")


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(CoverCommands.CLOSE))
async def close(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Close the cover."""
    await execute_platform_entity_command(server, client, message, "async_close_cover")


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        CoverCommands.SET_POSITION,
        {
            vol.Required(ATTR_POSITION): int,
        },
    )
)
async def set_position(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Set the cover position."""
    await execute_platform_entity_command(
        server, client, message, "async_set_cover_position"
    )


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(CoverCommands.STOP))
async def stop(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Stop the cover."""
    await execute_platform_entity_command(server, client, message, "async_stop_cover")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, open)
    register_api_command(server, close)
    register_api_command(server, set_position)
    register_api_command(server, stop)
