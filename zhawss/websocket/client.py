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
    MINIMAL_MESSAGE_SCHEMA,
    SUCCESS,
    WEBSOCKET_API,
    ZIGBEE_ERROR_CODE,
    MessageTypes,
)
from zhawss.websocket.types import ClientManagerType, ServerType

_LOGGER = logging.getLogger(__name__)


class Client:
    """ZHAWSS client implementation."""

    def __init__(
        self,
        websocket: WebSocketServerProtocol,
        client_manager: ClientManagerType,
    ):
        """Initialize the client."""
        self._websocket: WebSocketServerProtocol = websocket
        self._client_manager: ClientManagerType = client_manager
        self._receive_events: bool = False
        self._receive_raw_zcl_events: bool = False

    @property
    def is_connected(self) -> bool:
        """Return True if the websocket connection is connected."""
        return self._websocket.open

    def disconnect(self) -> None:
        """Disconnect this client and close the websocket."""
        asyncio.create_task(self._websocket.close())

    def send_event(self, message: dict[str, Any]) -> None:
        """Send event data to this client."""
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        self._send_data(message)

    def send_result_success(self, message_id: str, message: dict[str, Any]) -> None:
        """Send success result prompted by a client request."""
        message[SUCCESS] = True
        message[MESSAGE_ID] = message_id
        message[MESSAGE_TYPE] = MessageTypes.RESULT
        self._send_data(message)

    def send_result_error(
        self, message_id: str, error_code: str, message: dict[str, Any]
    ) -> None:
        """Send error result prompted by a client request."""
        message[SUCCESS] = False
        message[MESSAGE_ID] = message_id
        message[ERROR_CODE] = error_code
        message[MESSAGE_TYPE] = MessageTypes.RESULT
        self._send_data(message)

    def send_result_zigbee_error(
        self,
        message_id: str,
        error_code: str,
        zigbee_error_code: str,
        message: dict[str, Any],
    ) -> None:
        """Send zigbee error result prompted by a client zigbee request."""
        message[SUCCESS] = False
        message[MESSAGE_ID] = message_id
        message[ERROR_CODE] = error_code
        message[ZIGBEE_ERROR_CODE] = zigbee_error_code
        message[MESSAGE_TYPE] = MessageTypes.RESULT
        self._send_data(message)

    def _send_data(self, data: dict[str, Any]) -> None:
        """Send data to this client."""
        try:
            message = json.dumps(data)
            asyncio.create_task(self._websocket.send(message))
        except (TypeError) as exception:
            _LOGGER.error("Couldn't serialize data: %s", data, exc_info=exception)

    async def _handle_incoming_message(self, message) -> Awaitable[None]:
        """Handle an incoming message."""
        _LOGGER.info("Message received: %s", message)
        handlers: dict[str, Awaitable] = self._client_manager.server.data[WEBSOCKET_API]

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
            handler(self._client_manager.server, self, schema(msg))
        except Exception as err:  # pylint: disable=broad-except
            # TODO Fix this
            _LOGGER.error(
                "Error invoking handler: {}".format(msg[COMMAND]), exc_info=err
            )

    async def listen(self) -> Awaitable[None]:
        async for message in self._websocket:
            asyncio.create_task(self._handle_incoming_message(message))


class ClientManager:
    """ZHAWSS client manager implementation."""

    def __init__(self, server: ServerType):
        """Initialize the client."""
        self._server: ServerType = server
        self._clients: list[Client] = []

    @property
    def server(self) -> ServerType:
        """Return the server this ClientManager belongs to."""
        return self._server

    async def add_client(self, websocket) -> Awaitable[None]:
        """Adds a new client to the client manager."""
        client: Client = Client(websocket, self)
        self._clients.append(client)
        await client.listen()

    def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        for client in self._clients:
            if client.is_connected:
                _LOGGER.info(
                    "Broadcasting message: %s to client: %s",
                    message,
                    client._websocket.id,
                )
                """TODO use the receive flags on the client to determine if the client should receive the message"""
                client.send_event(message)
            else:
                client.disconnect()
                self._clients.remove(client)
