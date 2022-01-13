"""WS api for the alarm control panel platform entity."""
from typing import Any, Awaitable, Final

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import ATTR_UNIQUE_ID, IEEE, MESSAGE_ID
from zhawss.platforms import platform_entity_command_schema, send_result_success
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class AlarmControlPanelCommands(StrEnum):
    """Alarm control panel commands."""

    DISARM = "alarm_control_panel_disarm"
    ARM_HOME = "alarm_control_panel_arm_home"
    ARM_AWAY = "alarm_control_panel_arm_away"
    ARM_NIGHT = "alarm_control_panel_arm_night"
    TRIGGER = "alarm_control_panel_trigger"


ATTR_CODE: Final[str] = "code"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.DISARM,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
async def disarm(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Disarm the alarm control panel."""
    try:
        device = server.controller.get_device(message[IEEE])
        alarm_control_panel_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await alarm_control_panel_entity.async_alarm_disarm(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_HOME,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
async def arm_home(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Arm the alarm control panel in home mode."""
    try:
        device = server.controller.get_device(message[IEEE])
        alarm_control_panel_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await alarm_control_panel_entity.async_alarm_arm_home(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_AWAY,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
async def arm_away(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Arm the alarm control panel in away mode."""
    try:
        device = server.controller.get_device(message[IEEE])
        alarm_control_panel_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await alarm_control_panel_entity.async_alarm_arm_away(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_NIGHT,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
async def arm_night(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Arm the alarm control panel in night mode."""
    try:
        device = server.controller.get_device(message[IEEE])
        alarm_control_panel_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await alarm_control_panel_entity.async_alarm_arm_night(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.TRIGGER,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
async def trigger(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Trigger the alarm control panel."""
    try:
        device = server.controller.get_device(message[IEEE])
        alarm_control_panel_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await alarm_control_panel_entity.async_alarm_trigger(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, disarm)
    register_api_command(server, arm_home)
    register_api_command(server, arm_away)
    register_api_command(server, arm_night)
    register_api_command(server, trigger)
