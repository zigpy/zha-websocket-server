"""ZHAWSS websocket server."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import voluptuous
import websockets

from zhaws.server.const import COMMAND, APICommands
from zhaws.server.platforms import discovery
from zhaws.server.platforms.api import load_platform_entity_apis
from zhaws.server.platforms.discovery import PLATFORMS
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.client import ClientManager
from zhaws.server.zigbee.api import load_api as load_zigbee_controller_api
from zhaws.server.zigbee.controller import Controller

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client

_LOGGER = logging.getLogger(__name__)


class Server:
    """ZHAWSS server implementation."""

    def __init__(self) -> None:
        """Initialize the server."""
        self._waiter: asyncio.Future = asyncio.Future()
        self._controller: Controller = Controller(self)
        self._client_manager: ClientManager = ClientManager(self)
        self.data: dict[Any, Any] = {}
        for platform in PLATFORMS:
            self.data.setdefault(platform, [])
        self._register_api_commands()
        discovery.PROBE.initialize(self)
        discovery.GROUP_PROBE.initialize(self)

    @property
    def controller(self) -> Controller:
        """Return the zigbee application controller."""
        return self._controller

    @property
    def client_manager(self) -> ClientManager:
        """Return the zigbee application controller."""
        return self._client_manager

    async def start_server(self) -> None:
        """Stop the websocket server."""
        async with websockets.serve(  # type: ignore
            self._client_manager.add_client, "", 8001, logger=_LOGGER
        ):
            await self._waiter

    async def stop_server(self) -> None:
        """Stop the websocket server."""
        if self._controller.is_running:
            await self._controller.stop_network()
        self._waiter.set_result(True)

    def _register_api_commands(self) -> None:
        """Load server API commands."""
        from zhaws.server.websocket.client import load_api as load_client_api

        register_api_command(self, stop_server)
        load_zigbee_controller_api(self)
        load_platform_entity_apis(self)
        load_client_api(self)


@decorators.websocket_command(
    {
        voluptuous.Required(COMMAND): str(APICommands.STOP_SERVER),
    }
)
@decorators.async_response
async def stop_server(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Stop the Zigbee network."""
    await server.stop_server()
    client.send_result_success(message)
