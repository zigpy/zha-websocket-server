"""Client classes for zhawss."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

import voluptuous
from websockets.server import WebSocketServerProtocol

from zhaws.backports.enum import StrEnum
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

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server

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
        client_manager: ClientManager,
    ):
        """Initialize the client."""
        self._websocket: WebSocketServerProtocol = websocket
        self._client_manager: ClientManager = client_manager
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
        self, request_message: dict[str, Any], data: Optional[dict[str, Any]] = None
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
        error_message: str,
        zigbee_error_code: str,
    ) -> None:
        """Send zigbee error result prompted by a client zigbee request."""
        self.send_result_error(
            request_message={
                **request_message,
                ZIGBEE_ERROR_CODE: zigbee_error_code,
            },
            error_code="zigbee_error",
            error_message=error_message,
        )

    def _send_data(self, data: dict[str, Any]) -> None:
        """Send data to this client."""
        try:
            message = json.dumps(data)
        except TypeError as exc:
            _LOGGER.error("Couldn't serialize data: %s", data, exc_info=exc)
        else:
            asyncio.create_task(self._websocket.send(message))

    async def _handle_incoming_message(self, message: Union[str, bytes]) -> None:
        """Handle an incoming message."""
        _LOGGER.info("Message received: %s", message)
        handlers: dict[
            str, Tuple[Callable, Callable]
        ] = self._client_manager.server.data[WEBSOCKET_API]

        loaded_message = json.loads(message)
        _LOGGER.debug(
            "Received message: %s on websocket: %s", loaded_message, self._websocket.id
        )

        try:
            msg = MINIMAL_MESSAGE_SCHEMA(loaded_message)
        except voluptuous.Invalid as exception:
            _LOGGER.error(
                f"Received invalid command[unable to parse command]: {loaded_message}",
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
            _LOGGER.error("Error handling message: %s", msg, exc_info=err)
            self.send_result_error(
                loaded_message, "INTERNAL_ERROR", f"Internal error: {err}"
            )

    async def listen(self) -> None:
        async for message in self._websocket:
            asyncio.create_task(self._handle_incoming_message(message))

    def will_accept_message(self, message: dict[str, Any]) -> bool:
        """Checks if the client has registered to accept this type of message."""
        if not self.receive_events:
            return False

        if (
            message[EVENT_TYPE] == EventTypes.RAW_ZCL_EVENT
            and not self.receive_raw_zcl_events
        ):
            _LOGGER.info(
                "Client %s not accepting raw ZCL events: %s",
                self._websocket.id,
                message,
            )
            return False

        return True


@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.LISTEN_RAW_ZCL),
    }
)
@decorators.async_response
async def listen_raw_zcl(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Listen for raw ZCL events."""
    client.receive_raw_zcl_events = True
    client.send_result_success(message)


@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.LISTEN),
    }
)
@decorators.async_response
async def listen(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Listen for events."""
    client.receive_events = True
    client.send_result_success(message)


@decorators.websocket_command(
    {
        COMMAND: str(ClientAPICommands.DISCONNECT),
    }
)
@decorators.async_response
async def disconnect(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Disconnect the client."""
    client.disconnect()
    server.client_manager.remove_client(client)


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, listen_raw_zcl)
    register_api_command(server, listen)
    register_api_command(server, disconnect)


class ClientManager:
    """ZHAWSS client manager implementation."""

    def __init__(self, server: Server):
        """Initialize the client."""
        self._server: Server = server
        self._clients: list[Client] = []

    @property
    def server(self) -> Server:
        """Return the server this ClientManager belongs to."""
        return self._server

    async def add_client(self, websocket: WebSocketServerProtocol) -> None:
        """Adds a new client to the client manager."""
        client: Client = Client(websocket, self)
        self._clients.append(client)
        await client.listen()

    def remove_client(self, client: Client) -> None:
        """Removes a client from the client manager."""
        client.disconnect()
        self._clients.remove(client)

    def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        clients_to_remove = []

        for client in self._clients:
            if not client.is_connected:
                # XXX: We cannot remove elements from `_clients` while iterating over it
                clients_to_remove.append(client)
                continue

            if not client.will_accept_message(message):
                continue

            _LOGGER.info(
                "Broadcasting message: %s to client: %s",
                message,
                client._websocket.id,
            )
            """TODO use the receive flags on the client to determine if the client should receive the message"""
            client.send_event(message)

        for client in clients_to_remove:
            self.remove_client(client)
