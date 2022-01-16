"""WS API for the cover platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.platforms.cover import ATTR_POSITION
from zhaws.server.websocket.api import decorators, register_api_command

# open, close, set position, stop


if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class CoverCommands(StrEnum):
    """Cover commands."""

    OPEN = "cover_open"
    CLOSE = "cover_close"
    SET_POSITION = "cover_set_position"
    STOP = "cover_stop"


@decorators.websocket_command(platform_entity_command_schema(CoverCommands.OPEN))
@decorators.async_response
async def open(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Open the cover."""
    await execute_platform_entity_command(server, client, message, "async_open_cover")


@decorators.websocket_command(platform_entity_command_schema(CoverCommands.CLOSE))
@decorators.async_response
async def close(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Close the cover."""
    await execute_platform_entity_command(server, client, message, "async_close_cover")


@decorators.websocket_command(
    platform_entity_command_schema(
        CoverCommands.SET_POSITION,
        {
            vol.Required(ATTR_POSITION): int,
        },
    )
)
@decorators.async_response
async def set_position(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Set the cover position."""
    await execute_platform_entity_command(
        server, client, message, "async_set_cover_position"
    )


@decorators.websocket_command(platform_entity_command_schema(CoverCommands.STOP))
@decorators.async_response
async def stop(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Stop the cover."""
    await execute_platform_entity_command(server, client, message, "async_stop_cover")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, open)
    register_api_command(server, close)
    register_api_command(server, set_position)
    register_api_command(server, stop)
