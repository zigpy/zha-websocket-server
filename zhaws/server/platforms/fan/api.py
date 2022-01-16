"""WS API for the fan platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

ATTR_SPEED = "speed"
ATTR_PERCENTAGE = "percentage"
ATTR_PRESET_MODE = "preset_mode"


class FanAPICommands(StrEnum):
    """Light API commands."""

    TURN_ON = "fan_turn_on"
    TURN_OFF = "fan_turn_off"
    SET_PERCENTAGE = "fan_set_percentage"
    SET_PRESET_MODE = "fan_set_preset_mode"


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
@decorators.async_response
async def turn_on(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn fan on."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.websocket_command(platform_entity_command_schema(FanAPICommands.TURN_OFF))
@decorators.async_response
async def turn_off(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn fan off."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


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
@decorators.async_response
async def set_percentage(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the fan speed percentage."""
    await execute_platform_entity_command(
        server, client, message, "async_set_percentage"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        FanAPICommands.TURN_OFF,
        {
            vol.Required(ATTR_PRESET_MODE): str,
        },
    )
)
@decorators.async_response
async def set_preset_mode(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the fan preset mode."""
    await execute_platform_entity_command(
        server, client, message, "async_set_preset_mode"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
    register_api_command(server, set_percentage)
    register_api_command(server, set_preset_mode)
