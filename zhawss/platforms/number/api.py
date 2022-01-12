"""WS api for the number platform entity."""
from typing import Any, Awaitable

import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType
from zhawss.zigbee.device import ATTR_UNIQUE_ID

ATTR_VALUE = "value"
COMMAND_SET_VALUE = "number_set_value"


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_SET_VALUE,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Required(ATTR_VALUE): vol.Coerce(float),
    }
)
async def set_value(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Select an option."""
    try:
        device = server.controller.get_device(message[IEEE])
        number_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        value = message[ATTR_VALUE]
        await number_entity.async_set_value(value)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: COMMAND_SET_VALUE,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, set_value)
