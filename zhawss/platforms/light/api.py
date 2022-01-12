"""WS API for the light platform entity."""


from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
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
from zhawss.zigbee.device import ATTR_UNIQUE_ID


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
    {
        vol.Required(COMMAND): str(LightAPICommands.LIGHT_TURN_ON),
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
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
    }
)
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the light."""
    try:
        device = server.controller.get_device(message[IEEE])
        light_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await light_entity.async_turn_on(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: LightAPICommands.LIGHT_TURN_ON,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(LightAPICommands.LIGHT_TURN_OFF),
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_TRANSITION): VALID_TRANSITION,
        vol.Optional(ATTR_FLASH): VALID_FLASH,
    }
)
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the light."""
    try:
        device = server.controller.get_device(message[IEEE])
        light_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await light_entity.async_turn_off(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: LightAPICommands.LIGHT_TURN_OFF,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
