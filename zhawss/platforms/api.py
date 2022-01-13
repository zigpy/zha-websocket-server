"""WS API for common platform entity functionality."""
from typing import Any, Awaitable, Dict

import voluptuous as vol

from zhawss.const import ATTR_UNIQUE_ID, COMMAND, IEEE, MESSAGE_ID
from zhawss.websocket.types import ClientType, ServerType


def platform_entity_command_schema(
    command: str, schema: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Return the schema for a platform entity command."""
    full_schema = {
        vol.Required(COMMAND): str(command),
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
    if schema:
        full_schema.update(schema)
    return full_schema


async def execute_platform_entity_command(
    server: ServerType,
    client: ClientType,
    request_message: dict[str, Any],
    command: str,
) -> Awaitable[None]:
    """Get the platform entity and execute a command."""
    try:
        device = server.controller.get_device(request_message[IEEE])
        platform_entity = device.get_platform_entity(request_message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(request_message[MESSAGE_ID], str(err))
        return None

    try:
        action = getattr(platform_entity, command)
        await action(**request_message)
    except Exception as err:
        client.send_error(request_message[MESSAGE_ID], str(err))

    result = {}
    result[IEEE] = request_message[IEEE]
    result[ATTR_UNIQUE_ID] = request_message[ATTR_UNIQUE_ID]
    client.send_result_success(request_message, result)


def load_platform_entity_apis(server: ServerType):
    """Load the ws apis for all platform entities types."""
    from zhawss.platforms.light.api import load_api as load_light_api
    from zhawss.platforms.switch.api import load_api as load_switch_api

    load_light_api(server)
    load_switch_api(server)
