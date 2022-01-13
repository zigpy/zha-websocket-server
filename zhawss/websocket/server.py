"""ZHAWSS websocket server."""

import asyncio
import logging
from typing import Any, Awaitable

import voluptuous
import websockets

from zhawss.const import COMMAND, APICommands
from zhawss.platforms import discovery, load_platform_entity_apis
from zhawss.platforms.discovery import PLATFORMS
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.client import ClientManager
from zhawss.websocket.types import ClientType
from zhawss.zigbee.api import load_api as load_zigbee_controller_api
from zhawss.zigbee.controller import Controller
from zhawss.zigbee.types import ControllerType

_LOGGER = logging.getLogger(__name__)


class Server:
    """ZHAWSS server implementation."""

    def __init__(self):
        """Initialize the server."""
        self._waiter: asyncio.Future = asyncio.Future()
        self._controller: ControllerType = Controller(self)
        self._client_manager: ClientManager = ClientManager(self)
        self.data: dict[Any, Any] = {}
        for platform in PLATFORMS:
            self.data.setdefault(platform, [])
        self._register_api_commands()
        discovery.PROBE.initialize(self)

    @property
    def controller(self) -> ControllerType:
        """Return the zigbee application controller."""
        return self._controller

    @property
    def client_manager(self) -> ClientManager:
        """Return the zigbee application controller."""
        return self._client_manager

    async def start_server(self) -> Awaitable[None]:
        """Stop the websocket server."""
        async with websockets.serve(
            self._client_manager.add_client, "", 8001, logger=_LOGGER
        ):
            await self._waiter

    async def stop_server(self) -> Awaitable[None]:
        """Stop the websocket server."""
        if self._controller.is_running:
            await self._controller.stop_network()
        self._waiter.set_result(True)

    def _register_api_commands(self) -> None:
        """Load server API commands."""
        register_api_command(self, stop_server)
        load_zigbee_controller_api(self)
        load_platform_entity_apis(self)


@decorators.async_response
@decorators.websocket_command(
    {
        voluptuous.Required(COMMAND): str(APICommands.STOP_SERVER),
    }
)
async def stop_server(
    server: Server, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Stop the Zigbee network."""
    await server.stop_server()
    client.send_result_success(message)
