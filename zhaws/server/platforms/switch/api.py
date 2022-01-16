"""WS api for the switch platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class SwitchCommands(StrEnum):
    """Switch commands."""

    TURN_ON = "switch_turn_on"
    TURN_OFF = "switch_turn_off"


@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_ON))
@decorators.async_response
async def turn_on(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_OFF))
@decorators.async_response
async def turn_off(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
