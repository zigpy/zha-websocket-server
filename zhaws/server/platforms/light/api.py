"""WS API for the light platform entity."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import Field, validator

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


class LightTurnOnCommand(PlatformEntityCommand):
    """Light turn on command."""

    command: Literal[APICommands.LIGHT_TURN_ON] = APICommands.LIGHT_TURN_ON
    brightness: Annotated[int, Field(ge=0, le=255)] | None
    transition: Annotated[float, Field(ge=0, le=6553)] | None
    flash: Literal["short", "long"] | None
    effect: str | None
    hs_color: None | (
        tuple[Annotated[int, Field(ge=0, le=360)], Annotated[int, Field(ge=0, le=100)]]
    )
    color_temp: int | None

    @validator("color_temp", pre=True, always=True, each_item=False)
    def check_color_setting_exclusivity(
        cls, color_temp: int | None, values: dict[str, Any], **kwargs: Any
    ) -> int | None:
        """Ensure only one color mode is set."""
        if (
            "hs_color" in values
            and values["hs_color"] is not None
            and color_temp is not None
        ):
            raise ValueError('Only one of "hs_color" and "color_temp" can be set')
        return color_temp


@decorators.websocket_command(LightTurnOnCommand)
@decorators.async_response
async def turn_on(server: Server, client: Client, command: LightTurnOnCommand) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, command, "async_turn_on")


class LightTurnOffCommand(PlatformEntityCommand):
    """Light turn off command."""

    command: Literal[APICommands.LIGHT_TURN_OFF] = APICommands.LIGHT_TURN_OFF
    transition: Annotated[float, Field(ge=0, le=6553)] | None
    flash: Literal["short", "long"] | None


@decorators.websocket_command(LightTurnOffCommand)
@decorators.async_response
async def turn_off(
    server: Server, client: Client, command: LightTurnOffCommand
) -> None:
    """Turn on the light."""
    await execute_platform_entity_command(server, client, command, "async_turn_off")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
