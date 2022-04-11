"""WS api for the siren platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class SirenTurnOnCommand(PlatformEntityCommand):
    """Siren turn on command."""

    command: Literal[APICommands.SIREN_TURN_ON] = APICommands.SIREN_TURN_ON
    duration: Union[int, None]
    tone: Union[int, None]
    volume_level: Union[int, None]


@decorators.websocket_command(SirenTurnOnCommand)
@decorators.async_response
async def turn_on(server: Server, client: Client, command: SirenTurnOnCommand) -> None:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, command, "async_turn_on")


class SirenTurnOffCommand(PlatformEntityCommand):
    """Siren turn off command."""

    command: Literal[APICommands.SIREN_TURN_OFF] = APICommands.SIREN_TURN_OFF


@decorators.websocket_command(SirenTurnOffCommand)
@decorators.async_response
async def turn_off(
    server: Server, client: Client, command: SirenTurnOffCommand
) -> None:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, command, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
