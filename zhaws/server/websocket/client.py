"""Client classes for zhawss."""
import asyncio
import json
import logging
from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous
from websockets.server import WebSocketServerProtocol

from zhaws.server.const import (
    COMMAND,
    ERROR_CODE,
    ERROR_MESSAGE,
    EVENT_TYPE,
    MESSAGE_ID,
    MESSAGE_TYPE,
    MINIMAL_MESSAGE_SCHEMA,
    SUCCESS,
    WEBSOCKET_API,
    ZIGBEE_ERROR_CODE,
    EventTypes,
    MessageTypes,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.types import ClientManagerType, ServerType

_LOGGER = logging.getLogger(__name__)


class ClientAPICommands(StrEnum):
    """Enum for all client API commands."""

    LISTEN_RAW_ZCL = "client_listen_raw_zcl"
    LISTEN = "client_listen"
    DISCONNECT = "client_disconnect"


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
        self.receive_events: bool = False
        self.receive_raw_zcl_events: bool = False

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

    def send_result_success(
        self, request_message: dict[str, Any], data: dict[str, Any] = None
    ) -> None:
        """Send success result prompted by a client request."""
        message = {
            SUCCESS: True,
            MESSAGE_ID: request_message[MESSAGE_ID],
            MESSAGE_TYPE: MessageTypes.RESULT,
            COMMAND: request_message[COMMAND],
        }
        if data:
            message.update(data)
        self._send_data(message)

    def send_result_error(
        self, request_message: dict[str, Any], error_code: str, error_message: str
    ) -> None:
        """Send error result prompted by a client request."""
        message = {
            SUCCESS: False,
            MESSAGE_ID: request_message[MESSAGE_ID],
            MESSAGE_TYPE: MessageTypes.RESULT,
            COMMAND: request_message[COMMAND],
            ERROR_CODE: error_code,
            ERROR_MESSAGE: error_message,
        }
        self._send_data(message)

    def send_result_zigbee_error(
        self,
        request_message: dict[str, Any],
        error_code: str,
        error_message: str,
        zigbee_error_code: str,
    ) -> None:
        """Send zigbee error result prompted by a client zigbee request."""
        message = {
            SUCCESS: False,
            MESSAGE_ID: request_message[MESSAGE_ID],
            MESSAGE_TYPE: MessageTypes.RESULT,
            COMMAND: request_message[COMMAND],
            ERROR_CODE: error_code,
            ERROR_MESSAGE: error_message,
            ZIGBEE_ERROR_CODE: zigbee_error_code,
        }
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
        _LOGGER.debug(
            "Received message: %s on websocket: %s", message, self._websocket.id
        )

        try:
            msg = MINIMAL_MESSAGE_SCHEMA(message)
        except voluptuous.Invalid as exception:
            _LOGGER.error(
                f"Received invalid command[unable to parse command]: {message}",
                exc_info=exception,
            )
            return

        if msg[COMMAND] not in handlers:
            _LOGGER.error(
                f"Received invalid command[command not registered]: {msg[COMMAND]}"
            )
            return

        handler, schema = handlers[msg[COMMAND]]

        try:
            handler(self._client_manager.server, self, schema(msg))
        except Exception as err:  # pylint: disable=broad-except
            # TODO Fix this - make real error codes with error messages
            self.send_result_error(message, "INTERNAL_ERROR", f"Internal error: {err}")

    async def listen(self) -> Awaitable[None]:
        async for message in self._websocket:
            asyncio.create_task(self._handle_incoming_message(message))


@decorators.async_response
@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.LISTEN_RAW_ZCL),
    }
)
async def listen_raw_zcl(
    server: ServerType, client: Client, message: dict[str, Any]
) -> Awaitable[None]:
    """Listen for raw ZCL events."""
    client.receive_raw_zcl_events = True
    client.send_result_success(message)


@decorators.async_response
@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.LISTEN),
    }
)
async def listen(
    server: ServerType, client: Client, message: dict[str, Any]
) -> Awaitable[None]:
    """Listen for events."""
    client.receive_events = True
    client.send_result_success(message)


@decorators.async_response
@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.DISCONNECT),
    }
)
async def disconnect(
    server: ServerType, client: Client, message: dict[str, Any]
) -> Awaitable[None]:
    """Disconnect the client."""
    client.disconnect()
    server.client_manager.remove_client(client)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, listen_raw_zcl)
    register_api_command(server, listen)
    register_api_command(server, disconnect)


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

    def remove_client(self, client: Client) -> Awaitable[None]:
        """Adds a new client to the client manager."""
        self._clients.remove(client)

    def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        event_type = message[EVENT_TYPE]
        for client in self._clients:
            if client.is_connected:
                if client.receive_events:
                    if (
                        event_type == EventTypes.RAW_ZCL_EVENT
                        and not client.receive_raw_zcl_events
                    ):
                        _LOGGER.info(
                            "Not broadcasting message: %s to client: %s",
                            message,
                            client._websocket.id,
                        )
                        continue
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
