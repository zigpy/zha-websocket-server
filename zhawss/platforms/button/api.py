"""WS API for the button platform entity."""
from typing import Any, Awaitable

from zhawss.const import ATTR_UNIQUE_ID, IEEE, MESSAGE_ID
from zhawss.platforms import platform_entity_command_schema, send_result_success
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType

COMMAND_PRESS = "button_press"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(COMMAND_PRESS))
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

    send_result_success(client, message)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, press)
