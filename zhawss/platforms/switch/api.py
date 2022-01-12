"""WS api for the switch platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType
from zhawss.zigbee.device import ATTR_UNIQUE_ID


class SwitchCommands(StrEnum):
    """Switch commands."""

    TURN_ON = "switch_turn_on"
    TURN_OFF = "switch_turn_off"


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): SwitchCommands.TURN_ON,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    try:
        device = server.controller.get_device(message[IEEE])
        switch_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await switch_entity.async_turn_on()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: SwitchCommands.TURN_ON,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): SwitchCommands.TURN_OFF,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    try:
        device = server.controller.get_device(message[IEEE])
        switch_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await switch_entity.async_turn_off()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: SwitchCommands.TURN_OFF,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
