"""WS API for the cover platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class CoverOpenCommand(PlatformEntityCommand):
    """Cover open command."""

    command: Literal[APICommands.COVER_OPEN] = APICommands.COVER_OPEN


@decorators.websocket_command(CoverOpenCommand)
@decorators.async_response
async def open(server: Server, client: Client, command: CoverOpenCommand) -> None:
    """Open the cover."""
    await execute_platform_entity_command(server, client, command, "async_open_cover")


class CoverCloseCommand(PlatformEntityCommand):
    """Cover close command."""

    command: Literal[APICommands.COVER_CLOSE] = APICommands.COVER_CLOSE


@decorators.websocket_command(CoverCloseCommand)
@decorators.async_response
async def close(server: Server, client: Client, command: CoverCloseCommand) -> None:
    """Close the cover."""
    await execute_platform_entity_command(server, client, command, "async_close_cover")


class CoverSetPositionCommand(PlatformEntityCommand):
    """Cover set position command."""

    command: Literal[APICommands.COVER_SET_POSITION] = APICommands.COVER_SET_POSITION
    position: int


@decorators.websocket_command(CoverSetPositionCommand)
@decorators.async_response
async def set_position(
    server: Server, client: Client, command: CoverSetPositionCommand
) -> None:
    """Set the cover position."""
    await execute_platform_entity_command(
        server, client, command, "async_set_cover_position"
    )


class CoverStopCommand(PlatformEntityCommand):
    """Cover stop command."""

    command: Literal[APICommands.COVER_STOP] = APICommands.COVER_STOP


@decorators.websocket_command(CoverStopCommand)
@decorators.async_response
async def stop(server: Server, client: Client, command: CoverStopCommand) -> None:
    """Stop the cover."""
    await execute_platform_entity_command(server, client, command, "async_stop_cover")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, open)
    register_api_command(server, close)
    register_api_command(server, set_position)
    register_api_command(server, stop)
