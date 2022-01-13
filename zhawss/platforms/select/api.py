"""WS api for the select platform entity."""
from typing import Any, Awaitable, Union

import voluptuous as vol

from zhawss.const import ATTR_UNIQUE_ID, IEEE, MESSAGE_ID
from zhawss.platforms import platform_entity_command_schema, send_result_success
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType

ATTR_OPTION = "option"
COMMAND_SELECT_OPTION = "select_select_option"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        COMMAND_SELECT_OPTION,
        {
            vol.Required(ATTR_OPTION): Union[str, int],
        },
    )
)
async def select_option(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Select an option."""
    try:
        device = server.controller.get_device(message[IEEE])
        select_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        option = message[ATTR_OPTION]
        await select_entity.async_select_option(option)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, select_option)
