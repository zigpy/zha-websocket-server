"""WS API for the light platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, Optional

from pydantic import Field

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class LightTurnOnCommand(PlatformEntityCommand):
    """Light turn on command."""

    command: Literal[APICommands.LIGHT_TURN_ON] = APICommands.LIGHT_TURN_ON
    brightness: Optional[Annotated[int, Field(ge=0, le=255)]]
    transition: Optional[Annotated[float, Field(ge=0, le=6553)]]
    flash: Optional[Literal["short", "long"]]
    effect: Optional[str]
    hs_color: Optional[
        tuple[Annotated[int, Field(ge=0, le=360)], Annotated[int, Field(ge=0, le=100)]]
    ]
    color_temp: Optional[int]


@decorators.websocket_command(LightTurnOnCommand)
@decorators.async_response
async def turn_on(server: Server, client: Client, message: LightTurnOnCommand) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_on")


class LightTurnOffCommand(PlatformEntityCommand):
    """Light turn off command."""

    command: Literal[APICommands.LIGHT_TURN_OFF] = APICommands.LIGHT_TURN_OFF
    transition: Optional[Annotated[float, Field(ge=0, le=6553)]]
    flash: Optional[Literal["short", "long"]]


@decorators.websocket_command(LightTurnOffCommand)
@decorators.async_response
async def turn_off(
    server: Server, client: Client, message: LightTurnOffCommand
) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, message, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
