"""WS API for the fan platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, Union

from pydantic import Field

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class FanTurnOnCommand(PlatformEntityCommand):
    """Fan turn on command."""

    command: Literal[APICommands.FAN_TURN_ON] = APICommands.FAN_TURN_ON
    speed: Union[str, None]
    percentage: Union[Annotated[int, Field(ge=0, le=100)], None]
    preset_mode: Union[str, None]


@decorators.websocket_command(FanTurnOnCommand)
@decorators.async_response
async def turn_on(server: Server, client: Client, command: FanTurnOnCommand) -> None:
    """Turn fan on."""
    await execute_platform_entity_command(server, client, command, "async_turn_on")


class FanTurnOffCommand(PlatformEntityCommand):
    """Fan turn off command."""

    command: Literal[APICommands.FAN_TURN_OFF] = APICommands.FAN_TURN_OFF


@decorators.websocket_command(FanTurnOffCommand)
@decorators.async_response
async def turn_off(server: Server, client: Client, command: FanTurnOffCommand) -> None:
    """Turn fan off."""
    await execute_platform_entity_command(server, client, command, "async_turn_off")


class FanSetPercentageCommand(PlatformEntityCommand):
    """Fan set percentage command."""

    command: Literal[APICommands.FAN_SET_PERCENTAGE] = APICommands.FAN_SET_PERCENTAGE
    percentage: Annotated[int, Field(ge=0, le=100)]


@decorators.websocket_command(FanSetPercentageCommand)
@decorators.async_response
async def set_percentage(
    server: Server, client: Client, command: FanSetPercentageCommand
) -> None:
    """Set the fan speed percentage."""
    await execute_platform_entity_command(
        server, client, command, "async_set_percentage"
    )


class FanSetPresetModeCommand(PlatformEntityCommand):
    """Fan set preset mode command."""

    command: Literal[APICommands.FAN_SET_PRESET_MODE] = APICommands.FAN_SET_PRESET_MODE
    preset_mode: str


@decorators.websocket_command(FanSetPresetModeCommand)
@decorators.async_response
async def set_preset_mode(
    server: Server, client: Client, command: FanSetPresetModeCommand
) -> None:
    """Set the fan preset mode."""
    await execute_platform_entity_command(
        server, client, command, "async_set_preset_mode"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
    register_api_command(server, set_percentage)
    register_api_command(server, set_preset_mode)
