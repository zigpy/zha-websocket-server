"""WS api for the switch platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class SwitchTurnOnCommand(PlatformEntityCommand):
    """Switch turn on command."""

    command: Literal[APICommands.SWITCH_TURN_ON] = APICommands.SWITCH_TURN_ON


@decorators.websocket_command(SwitchTurnOnCommand)
@decorators.async_response
async def turn_on(server: Server, client: Client, command: SwitchTurnOnCommand) -> None:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, command, "async_turn_on")


class SwitchTurnOffCommand(PlatformEntityCommand):
    """Switch turn off command."""

    command: Literal[APICommands.SWITCH_TURN_OFF] = APICommands.SWITCH_TURN_OFF


@decorators.websocket_command(SwitchTurnOffCommand)
@decorators.async_response
async def turn_off(
    server: Server, client: Client, command: SwitchTurnOffCommand
) -> None:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, command, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
