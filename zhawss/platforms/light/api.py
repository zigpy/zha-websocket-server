"""WS API for the light platform entity."""


from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.platforms.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


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


@decorators.async_response
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
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        LightAPICommands.LIGHT_TURN_OFF,
        {
            vol.Optional(ATTR_TRANSITION): VALID_TRANSITION,
            vol.Optional(ATTR_FLASH): VALID_FLASH,
        },
    )
)
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
