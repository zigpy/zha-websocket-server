"""WS API for the light platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.platforms.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class LightAPICommands(StrEnum):
    """Light API commands."""

    LIGHT_TURN_ON = "light_turn_on"
    LIGHT_TURN_OFF = "light_turn_off"


COLOR_GROUP = "Color descriptors"

FLASH_SHORT = "short"
FLASH_LONG = "long"

VALID_TRANSITION = vol.All(vol.Coerce(float), vol.Clamp(min=0, max=6553))
VALID_BRIGHTNESS = vol.All(vol.Coerce(int), vol.Clamp(min=0, max=255))
VALID_FLASH = vol.In([FLASH_SHORT, FLASH_LONG])


@decorators.websocket_command(
    platform_entity_command_schema(
        LightAPICommands.LIGHT_TURN_ON,
        {
            vol.Optional(ATTR_BRIGHTNESS): VALID_BRIGHTNESS,
            vol.Optional(ATTR_TRANSITION): VALID_TRANSITION,
            vol.Optional(ATTR_FLASH): VALID_FLASH,
            vol.Optional(ATTR_EFFECT): str,
            vol.Exclusive(ATTR_HS_COLOR, COLOR_GROUP): vol.All(
                vol.Coerce(tuple),
                vol.ExactSequence(
                    (
                        vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                        vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
                    )
                ),
            ),
            vol.Exclusive(ATTR_COLOR_TEMP, COLOR_GROUP): vol.All(
                vol.Coerce(int), vol.Range(min=1)
            ),
        },
    )
)
@decorators.async_response
async def turn_on(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.websocket_command(
    platform_entity_command_schema(
        LightAPICommands.LIGHT_TURN_OFF,
        {
            vol.Optional(ATTR_TRANSITION): VALID_TRANSITION,
            vol.Optional(ATTR_FLASH): VALID_FLASH,
        },
    )
)
@decorators.async_response
async def turn_off(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
