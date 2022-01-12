"""WS API for the button platform entity."""


from typing import Any, Awaitable

import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType
from zhawss.zigbee.device import ATTR_UNIQUE_ID

COMMAND_PRESS = "button_press"


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_PRESS,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def press(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the button."""
    try:
        device = server.controller.get_device(message[IEEE])
        button_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await button_entity.async_press()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: COMMAND_PRESS,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, press)
