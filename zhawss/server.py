"""ZHAWSS websocket server."""

import asyncio
import logging
from typing import Any

import voluptuous
import websockets

from zhawss.client import ClientManager
from zhawss.const import COMMAND, MESSAGE_ID, APICommands
from zhawss.types import ClientType, ControllerType
from zhawss.websocket_api import async_register_command, decorators
from zhawss.zigbee.api import load_api as load_zigbee_controller_api
from zhawss.zigbee.application import Controller

_LOGGER = logging.getLogger(__name__)


class Server:
    """ZHAWSS server implementation."""

    def __init__(self):
        """Initialize the server."""
        self._waiter: asyncio.Future = asyncio.Future()
        self._controller: ControllerType = Controller()
        self._client_manager: ClientManager = ClientManager(self)
        self.data: dict[str, Any] = {}
        self._register_api_commands()

    @property
    def controller(self) -> ControllerType:
        """Return the zigbee application controller."""
        return self._controller

    @property
    def client_manager(self) -> ClientManager:
        """Return the zigbee application controller."""
        return self._client_manager

    async def start_server(self):
        """Stop the websocket server."""
        async with websockets.serve(
            self._client_manager.add_client, "", 8001, logger=_LOGGER
        ):
            await self._waiter

    def stop_server(self):
        """Stop the websocket server."""
        self._waiter.set_result(True)

    def _register_api_commands(self):
        """Load server API commands."""
        async_register_command(self, stop_server)
        load_zigbee_controller_api(self)


@decorators.websocket_command(
    {
        voluptuous.Required(COMMAND): str(APICommands.STOP_SERVER),
    }
)
def stop_server(server: Server, client: ClientType, message: dict[str, Any]) -> None:
    """Stop the Zigbee network."""
    server.stop_server()
    client.send_result_success(message[MESSAGE_ID], {})
