"""WS api for the alarm control panel platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class AlarmControlPanelCommands(StrEnum):
    """Alarm control panel commands."""

    DISARM = "alarm_control_panel_disarm"
    ARM_HOME = "alarm_control_panel_arm_home"
    ARM_AWAY = "alarm_control_panel_arm_away"
    ARM_NIGHT = "alarm_control_panel_arm_night"
    TRIGGER = "alarm_control_panel_trigger"


ATTR_CODE: Final[str] = "code"


@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.DISARM,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
@decorators.async_response
async def disarm(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Disarm the alarm control panel."""
    await execute_platform_entity_command(server, client, message, "async_alarm_disarm")


@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_HOME,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
@decorators.async_response
async def arm_home(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Arm the alarm control panel in home mode."""
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_home"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_AWAY,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
@decorators.async_response
async def arm_away(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Arm the alarm control panel in away mode."""
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_away"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.ARM_NIGHT,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
@decorators.async_response
async def arm_night(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Arm the alarm control panel in night mode."""
    await execute_platform_entity_command(
        server, client, message, "async_alarm_arm_night"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        AlarmControlPanelCommands.TRIGGER,
        {
            vol.Optional(ATTR_CODE): str,
        },
    )
)
@decorators.async_response
async def trigger(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Trigger the alarm control panel."""
    await execute_platform_entity_command(
        server, client, message, "async_alarm_trigger"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, disarm)
    register_api_command(server, arm_home)
    register_api_command(server, arm_away)
    register_api_command(server, arm_night)
    register_api_command(server, trigger)
