"""Client classes for zhawss."""
import asyncio
import json
import logging
from typing import Any, Awaitable

import voluptuous
from websockets.server import WebSocketServerProtocol

from zhawss.const import (
    COMMAND,
    ERROR_CODE,
    MESSAGE_ID,
    MESSAGE_TYPE,
    MESSAGE_TYPE_EVENT,
    MESSAGE_TYPE_RESULT,
    MINIMAL_MESSAGE_SCHEMA,
    SUCCESS,
    WEBSOCKET_API,
    ZIGBEE_ERROR_CODE,
)
from zhawss.types import ControllerType

_LOGGER = logging.getLogger(__name__)


class Client:
    """ZHAWSS client implementation."""

    def __init__(
        self,
        websocket: WebSocketServerProtocol,
        client_manager,
        controller: ControllerType,
    ):
        """Initialize the client."""
        self._websocket: WebSocketServerProtocol = websocket
        self._client_manager: ClientManager = client_manager
        self._controller: ControllerType = controller

    @property
    def is_connected(self):
        """Return True if the websocket connection is connected."""
        return self._websocket.open

    def disconnect(self):
        """Disconnect this client and close the websocket."""
        asyncio.create_task(self._websocket.close())

    def send_event(self, message: dict[str, Any]):
        """Send event data to this client."""
        message[MESSAGE_TYPE] = MESSAGE_TYPE_EVENT
        self._send_data(message)

    def send_result_success(self, message_id: str, message: dict[str, Any]):
        """Send success result prompted by a client request."""
        message[SUCCESS] = True
        message[MESSAGE_ID] = message_id
        message[MESSAGE_TYPE] = MESSAGE_TYPE_RESULT
        self._send_data(message)

    def send_result_error(
        self, message_id: str, error_code: str, message: dict[str, Any]
    ):
        """Send error result prompted by a client request."""
        message[SUCCESS] = False
        message[MESSAGE_ID] = message_id
        message[ERROR_CODE] = error_code
        message[MESSAGE_TYPE] = MESSAGE_TYPE_RESULT
        self._send_data(message)

    def send_result_zigbee_error(
        self,
        message_id: str,
        error_code: str,
        zigbee_error_code: str,
        message: dict[str, Any],
    ):
        """Send zigbee error result prompted by a client zigbee request."""
        message[SUCCESS] = False
        message[MESSAGE_ID] = message_id
        message[ERROR_CODE] = error_code
        message[ZIGBEE_ERROR_CODE] = zigbee_error_code
        message[MESSAGE_TYPE] = MESSAGE_TYPE_RESULT
        self._send_data(message)

    def _send_data(self, data: dict[str, Any]):
        """Send data to this client."""
        try:
            message = json.dumps(data)
            asyncio.create_task(self._websocket.send(message))
        except (TypeError) as exception:
            _LOGGER.error("Couldn't serialize data: %s", data, exc_info=exception)

    async def _handle_incoming_message(self, message):
        """Handle an incoming message."""
        _LOGGER.info("Message received: %s", message)
        handlers: dict[str, Awaitable] = self._controller.data[WEBSOCKET_API]

        message = json.loads(message)
        _LOGGER.info(
            "Received message: %s on websocket: %s", message, self._websocket.id
        )

        try:
            msg = MINIMAL_MESSAGE_SCHEMA(message)
        except voluptuous.Invalid:
            _LOGGER.error("Received invalid command", message)
            return

        if msg[COMMAND] not in handlers:
            _LOGGER.error("Received invalid command: {}".format(msg[COMMAND]))
            return

        handler, schema = handlers[msg[COMMAND]]

        try:
            handler(self._controller, self, schema(msg))
        except Exception as err:  # pylint: disable=broad-except
            # TODO Fix this
            _LOGGER.error(
                "Error invoking handler: {}".format(msg[COMMAND]), exc_info=err
            )

    async def listen(self) -> None:
        async for message in self._websocket:
            asyncio.create_task(self._handle_incoming_message(message))


class ClientManager:
    """ZHAWSS client manager implementation."""

    def __init__(self, controller: ControllerType):
        """Initialize the client."""
        self._clients: list[Client] = []
        self._controller: ControllerType = controller

    async def add_client(self, websocket):
        """Adds a new client to the client manager."""
        client: Client = Client(websocket, self, self._controller)
        self._clients.append(client)
        await client.listen()
