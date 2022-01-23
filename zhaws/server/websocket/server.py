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
        self._ws_server: websockets.Serve | None = None
        self._controller: Controller = Controller(self)
        self._client_manager: ClientManager = ClientManager(self)
        self._stopped_event: asyncio.Event = asyncio.Event()
        self.data: dict[Any, Any] = {}
        for platform in PLATFORMS:
            self.data.setdefault(platform, [])
        self._register_api_commands()
        discovery.PROBE.initialize(self)
        discovery.GROUP_PROBE.initialize(self)

    @property
    def is_serving(self) -> bool:
        """Returns whether or not the websocket server is serving."""
        return self._ws_server is not None and self._ws_server.is_serving

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
        assert self._ws_server is None
        self._stopped_event.clear()
        self._ws_server = await websockets.serve(
            self.client_manager.add_client, self._host, self._port, logger=_LOGGER
        )

    async def wait_closed(self) -> None:
        """Waits until the server is not running."""
        return await self._stopped_event.wait()

    async def stop_server(self) -> None:
        """Stop the websocket server."""
        if self._ws_server is None:
            self._stopped_event.set()
            return

        assert self._ws_server is not None

        if self._controller.is_running:
            await self._controller.stop_network()

        self._ws_server.close()
        await self._ws_server.wait_closed()
        self._ws_server = None

        self._stopped_event.set()

    async def __aenter__(self) -> Server:
        await self.start_server()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        await self.stop_server()

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
    client.send_result_success(message)
    await server.stop_server()
