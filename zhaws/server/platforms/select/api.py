"""WS api for the select platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from zhaws.server.const import APICommands
from zhaws.server.platforms import PlatformEntityCommand
from zhaws.server.platforms.api import execute_platform_entity_command
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class SelectSelectOptionCommand(PlatformEntityCommand):
    """Select select option command."""

    command: Literal[
        APICommands.SELECT_SELECT_OPTION
    ] = APICommands.SELECT_SELECT_OPTION
    option: str


@decorators.websocket_command(SelectSelectOptionCommand)
@decorators.async_response
async def select_option(
    server: Server, client: Client, message: SelectSelectOptionCommand
) -> None:
    """Select an option."""
    await execute_platform_entity_command(
        server, client, message, "async_select_option"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, select_option)
