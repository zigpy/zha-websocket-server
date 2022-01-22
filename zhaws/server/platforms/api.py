"""WS API for common platform entity functionality."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.const import ATTR_UNIQUE_ID, COMMAND, IEEE
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


class PlatformEntityCommands(StrEnum):
    """Enumeration of platform entity commands."""

    REFRESH_STATE = "platform_entity_refresh_state"


def platform_entity_command_schema(
    command: str, schema: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Return the schema for a platform entity command."""
    full_schema = {
        vol.Required(COMMAND): str(command),
        vol.Optional(IEEE): str,
        vol.Optional("group_id"): int,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
    if schema:
        full_schema.update(schema)
    return full_schema


async def execute_platform_entity_command(
    server: Server,
    client: Client,
    request_message: dict[str, Any],
    command: str,
) -> None:
    """Get the platform entity and execute a command."""
    try:
        if IEEE in request_message:
            device = server.controller.get_device(request_message[IEEE])
            platform_entity: Any = device.get_platform_entity(
                request_message[ATTR_UNIQUE_ID]
            )
        else:
            group = server.controller.get_group(request_message["group_id"])
            platform_entity = group.group_entities[request_message[ATTR_UNIQUE_ID]]
    except ValueError as err:
        _LOGGER.exception("Error executing command: %s", command, exc_info=err)
        client.send_result_error(
            request_message, "PLATFORM_ENTITY_COMMAND_ERROR", str(err)
        )
        return None

    try:
        action = getattr(platform_entity, command)
        if action.__code__.co_argcount == 1:  # the only argument is self
            await action()
        else:
            await action(**request_message)
    except Exception as err:
        _LOGGER.exception("Error executing command: %s", command, exc_info=err)
        client.send_result_error(
            request_message, "PLATFORM_ENTITY_ACTION_ERROR", str(err)
        )

    result = {}
    if IEEE in request_message:
        result[IEEE] = request_message[IEEE]
    else:
        result["group_id"] = request_message["group_id"]
    result[ATTR_UNIQUE_ID] = request_message[ATTR_UNIQUE_ID]
    client.send_result_success(request_message, result)


@decorators.websocket_command(
    platform_entity_command_schema(PlatformEntityCommands.REFRESH_STATE)
)
@decorators.async_response
async def refresh_state(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Refresh the state of the platform entity."""
    await execute_platform_entity_command(server, client, message, "async_update")


def load_platform_entity_apis(server: Server) -> None:
    """Load the ws apis for all platform entities types."""
    from zhaws.server.platforms.alarm_control_panel.api import (
        load_api as load_alarm_control_panel_api,
    )
    from zhaws.server.platforms.button.api import load_api as load_button_api
    from zhaws.server.platforms.climate.api import load_api as load_climate_api
    from zhaws.server.platforms.cover.api import load_api as load_cover_api
    from zhaws.server.platforms.fan.api import load_api as load_fan_api
    from zhaws.server.platforms.light.api import load_api as load_light_api
    from zhaws.server.platforms.lock.api import load_api as load_lock_api
    from zhaws.server.platforms.number.api import load_api as load_number_api
    from zhaws.server.platforms.select.api import load_api as load_select_api
    from zhaws.server.platforms.siren.api import load_api as load_siren_api
    from zhaws.server.platforms.switch.api import load_api as load_switch_api

    register_api_command(server, refresh_state)
    load_alarm_control_panel_api(server)
    load_button_api(server)
    load_climate_api(server)
    load_cover_api(server)
    load_fan_api(server)
    load_light_api(server)
    load_lock_api(server)
    load_number_api(server)
    load_select_api(server)
    load_siren_api(server)
    load_switch_api(server)
