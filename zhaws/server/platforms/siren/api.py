"""WS api for the siren platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.platforms.siren import ATTR_DURATION, ATTR_TONE, ATTR_VOLUME_LEVEL
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class SirenCommands(StrEnum):
    """Siren commands."""

    TURN_ON = "siren_turn_on"
    TURN_OFF = "siren_turn_off"


@decorators.websocket_command(
    platform_entity_command_schema(
        SirenCommands.TURN_ON,
        {
            vol.Optional(ATTR_DURATION): int,
            vol.Optional(ATTR_VOLUME_LEVEL): int,
            vol.Optional(ATTR_TONE): str,
        },
    )
)
@decorators.async_response
async def turn_on(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.websocket_command(platform_entity_command_schema(SirenCommands.TURN_OFF))
@decorators.async_response
async def turn_off(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
