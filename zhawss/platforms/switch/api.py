"""WS api for the switch platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class SwitchCommands(StrEnum):
    """Switch commands."""

    TURN_ON = "switch_turn_on"
    TURN_OFF = "switch_turn_off"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_ON))
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_OFF))
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
