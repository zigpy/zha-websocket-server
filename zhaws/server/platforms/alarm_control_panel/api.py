"""WS api for the alarm control panel platform entity."""
from typing import Any, Awaitable, Final

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.types import ClientType, ServerType


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
    await execute_platform_entity_command(server, client, message, "async_alarm_disarm")


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
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_home"
    )


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
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_away"
    )


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
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_night"
    )


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
    await execute_platform_entity_command(
        server, client, message, "async_alarm_trigger"
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, disarm)
    register_api_command(server, arm_home)
    register_api_command(server, arm_away)
    register_api_command(server, arm_night)
    register_api_command(server, trigger)
