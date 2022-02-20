"""WS api for the number platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

ATTR_VALUE = "value"
COMMAND_SET_VALUE = "number_set_value"


class NumberSetValueCommand(PlatformEntityCommand):
    """Number set value command."""

    command: Literal[APICommands.NUMBER_SET_VALUE] = APICommands.NUMBER_SET_VALUE
    value: float


@decorators.websocket_command(NumberSetValueCommand)
@decorators.async_response
async def set_value(
    server: Server, client: Client, message: NumberSetValueCommand
) -> None:
    """Select an option."""
    await execute_platform_entity_command(server, client, message, "async_set_value")


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, set_value)
