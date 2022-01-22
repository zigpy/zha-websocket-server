"""ZHAWSS websocket server."""
from __future__ import annotations

import asyncio
import logging
from types import TracebackType
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

    def __init__(self, *, host: str = "", port: int = 8001) -> None:
        """Initialize the server."""
        self._host: str = host
        self._port: int = port
        self._server: websockets.Serve | None = None
        self._stop_event: asyncio.Event = asyncio.Event()
        self._controller: Controller = Controller(self)
        self._client_manager: ClientManager = ClientManager(self)
        self.data: dict[Any, Any] = {}
        for platform in PLATFORMS:
            self.data.setdefault(platform, [])
        self._register_api_commands()
        discovery.PROBE.initialize(self)
        discovery.GROUP_PROBE.initialize(self)

    async def __aenter__(self) -> Server:
        assert self._server is None

        self._server = websockets.serve(
            self._client_manager.add_client, self._host, self._port, logger=_LOGGER
        )
        await self._server.__aenter__()

        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        assert self._server is not None

        await self.stop_server()
        await self._server.__aexit__(exc_type, exc_value, traceback)
        self._server = None

    @property
    def controller(self) -> Controller:
        """Return the zigbee application controller."""
        return self._controller

    @property
    def client_manager(self) -> ClientManager:
        """Return the zigbee application controller."""
        return self._client_manager

    async def start_server(self) -> None:
        """Start the websocket server."""
        self._stop_event.clear()

        async with self:
            await self._stop_event

    async def stop_server(self) -> None:
        """Stop the websocket server."""
        if self._controller.is_running:
            await self._controller.stop_network()
        self._stop_event.set()

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
