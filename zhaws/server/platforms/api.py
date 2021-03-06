"""WS API for common platform entity functionality."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from zhaws.server.const import ATTR_UNIQUE_ID, IEEE, APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


async def execute_platform_entity_command(
    server: Server,
    client: Client,
    command: PlatformEntityCommand,
    method_name: str,
) -> None:
    """Get the platform entity and execute a method based on the command."""
    try:
        if command.ieee:
            _LOGGER.debug("command: %s", command)
            device = server.controller.get_device(command.ieee)
            platform_entity: Any = device.get_platform_entity(command.unique_id)
        else:
            assert command.group_id
            group = server.controller.get_group(command.group_id)
            platform_entity = group.group_entities[command.unique_id]
    except ValueError as err:
        _LOGGER.exception(
            "Error executing command: %s method_name: %s",
            command,
            method_name,
            exc_info=err,
        )
        client.send_result_error(command, "PLATFORM_ENTITY_COMMAND_ERROR", str(err))
        return None

    try:
        action = getattr(platform_entity, method_name)
        if action.__code__.co_argcount == 1:  # the only argument is self
            await action()
        else:
            await action(**command.dict(exclude_none=True))
    except Exception as err:
        _LOGGER.exception("Error executing command: %s", method_name, exc_info=err)
        client.send_result_error(command, "PLATFORM_ENTITY_ACTION_ERROR", str(err))
        return

    result: dict[str, Any] = {}
    if command.ieee:
        result[IEEE] = str(command.ieee)
    else:
        result["group_id"] = command.group_id
    result[ATTR_UNIQUE_ID] = command.unique_id
    client.send_result_success(command, result)


class PlatformEntityRefreshStateCommand(PlatformEntityCommand):
    """Platform entity refresh state command."""

    command: Literal[
        APICommands.PLATFORM_ENTITY_REFRESH_STATE
    ] = APICommands.PLATFORM_ENTITY_REFRESH_STATE


@decorators.websocket_command(PlatformEntityRefreshStateCommand)
@decorators.async_response
async def refresh_state(
    server: Server, client: Client, command: PlatformEntityCommand
) -> None:
    """Refresh the state of the platform entity."""
    await execute_platform_entity_command(server, client, command, "async_update")


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
