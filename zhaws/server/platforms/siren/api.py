"""WS api for the siren platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.platforms.siren import ATTR_DURATION, ATTR_TONE, ATTR_VOLUME_LEVEL
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.types import ClientType, ServerType


class SirenCommands(StrEnum):
    """Siren commands."""

    TURN_ON = "siren_turn_on"
    TURN_OFF = "siren_turn_off"


@decorators.async_response
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
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SirenCommands.TURN_OFF))
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the siren."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
