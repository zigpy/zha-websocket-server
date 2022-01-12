"""WS api for the alarm control panel platform entity."""

# disarm, arm home, arm away, arm night, trigger
from typing import Any, Awaitable, Final

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType
from zhawss.zigbee.device import ATTR_UNIQUE_ID


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
    {
        vol.Required(COMMAND): AlarmControlPanelCommands.DISARM,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_CODE): str,
    }
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

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: AlarmControlPanelCommands.DISARM,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): AlarmControlPanelCommands.ARM_HOME,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_CODE): str,
    }
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

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: AlarmControlPanelCommands.ARM_HOME,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): AlarmControlPanelCommands.ARM_AWAY,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_CODE): str,
    }
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

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: AlarmControlPanelCommands.ARM_AWAY,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): AlarmControlPanelCommands.ARM_NIGHT,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_CODE): str,
    }
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

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: AlarmControlPanelCommands.ARM_NIGHT,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): AlarmControlPanelCommands.TRIGGER,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Optional(ATTR_CODE): str,
    }
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

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: AlarmControlPanelCommands.TRIGGER,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, disarm)
    register_api_command(server, arm_home)
    register_api_command(server, arm_away)
    register_api_command(server, arm_night)
    register_api_command(server, trigger)
