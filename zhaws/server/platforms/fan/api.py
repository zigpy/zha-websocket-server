"""WS API for the fan platform entity."""
from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.types import ClientType, ServerType

ATTR_SPEED = "speed"
ATTR_PERCENTAGE = "percentage"
ATTR_PRESET_MODE = "preset_mode"


class FanAPICommands(StrEnum):
    """Light API commands."""

    TURN_ON = "fan_turn_on"
    TURN_OFF = "fan_turn_off"
    SET_PERCENTAGE = "fan_set_percentage"
    SET_PRESET_MODE = "fan_set_preset_mode"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        FanAPICommands.TURN_ON,
        {
            vol.Optional(ATTR_SPEED): str,
            vol.Optional(ATTR_PERCENTAGE): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional(ATTR_PRESET_MODE): str,
        },
    )
)
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn fan on."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(FanAPICommands.TURN_OFF))
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn fan off."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        FanAPICommands.SET_PERCENTAGE,
        {
            vol.Required(ATTR_PERCENTAGE): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
        },
    )
)
async def set_percentage(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Set the fan speed percentage."""
    await execute_platform_entity_command(
        server, client, message, "async_set_percentage"
    )


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        FanAPICommands.TURN_OFF,
        {
            vol.Required(ATTR_PRESET_MODE): str,
        },
    )
)
async def set_preset_mode(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Set the fan preset mode."""
    await execute_platform_entity_command(
        server, client, message, "async_set_preset_mode"
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
    register_api_command(server, set_percentage)
    register_api_command(server, set_preset_mode)
