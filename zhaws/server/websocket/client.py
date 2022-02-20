"""Client classes for zhawss."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, Tuple

from pydantic import ValidationError
from websockets.server import WebSocketServerProtocol

from zhaws.server.const import (
    COMMAND,
    ERROR_CODE,
    ERROR_MESSAGE,
    EVENT_TYPE,
    MESSAGE_ID,
    MESSAGE_TYPE,
    SUCCESS,
    WEBSOCKET_API,
    ZIGBEE_ERROR_CODE,
    APICommands,
    EventTypes,
    MessageTypes,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.api.model import WebSocketCommand

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


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
        self._client_manager.server.track_task(
            asyncio.create_task(self._websocket.close())
        )

    def send_event(self, message: dict[str, Any]) -> None:
        """Send event data to this client."""
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        self._send_data(message)

    def send_result_success(
        self, request_message: WebSocketCommand, data: Optional[dict[str, Any]] = None
    ) -> None:
        """Send success result prompted by a client request."""
        message = {
            SUCCESS: True,
            MESSAGE_ID: request_message.message_id,
            MESSAGE_TYPE: MessageTypes.RESULT,
            COMMAND: request_message.command,
        }
        if data:
            message.update(data)
        self._send_data(message)

    def send_result_error(
        self,
        request_message: WebSocketCommand,
        error_code: str,
        error_message: str,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Send error result prompted by a client request."""
        message = {
            SUCCESS: False,
            MESSAGE_ID: request_message.message_id,
            MESSAGE_TYPE: MessageTypes.RESULT,
            COMMAND: request_message.command,
            ERROR_CODE: error_code,
            ERROR_MESSAGE: error_message,
            **(data or {}),
        }
        self._send_data(message)

    def send_result_zigbee_error(
        self,
        request_message: WebSocketCommand,
        error_message: str,
        zigbee_error_code: str,
    ) -> None:
        """Send zigbee error result prompted by a client zigbee request."""
        self.send_result_error(
            request_message,
            error_code="zigbee_error",
            error_message=error_message,
            data={ZIGBEE_ERROR_CODE: zigbee_error_code},
        )

    def _send_data(self, data: dict[str, Any]) -> None:
        """Send data to this client."""
        try:
            message = json.dumps(data)
        except TypeError as exc:
            _LOGGER.error("Couldn't serialize data: %s", data, exc_info=exc)
        else:
            self._client_manager.server.track_task(
                asyncio.create_task(self._websocket.send(message))
            )

    async def _handle_incoming_message(self, message: str | bytes) -> None:
        """Handle an incoming message."""
        _LOGGER.info("Message received: %s", message)
        handlers: dict[
            str, Tuple[Callable, WebSocketCommand]
        ] = self._client_manager.server.data[WEBSOCKET_API]

        loaded_message = json.loads(message)
        _LOGGER.debug(
            "Received message: %s on websocket: %s", loaded_message, self._websocket.id
        )

        try:
            msg = WebSocketCommand.parse_obj(loaded_message)
        except ValidationError as exception:
            _LOGGER.error(
                f"Received invalid command[unable to parse command]: {loaded_message}",
                exc_info=exception,
            )
            return

        if msg.command not in handlers:
            _LOGGER.error(
                f"Received invalid command[command not registered]: {msg.command}"
            )
            return

        handler, model = handlers[msg.command]

        try:
            handler(self._client_manager.server, self, model.parse_obj(loaded_message))
        except Exception as err:  # pylint: disable=broad-except
            # TODO Fix this - make real error codes with error messages
            _LOGGER.error("Error handling message: %s", loaded_message, exc_info=err)
            self.send_result_error(
                loaded_message, "INTERNAL_ERROR", f"Internal error: {err}"
            )

    async def listen(self) -> None:
        async for message in self._websocket:
            self._client_manager.server.track_task(
                asyncio.create_task(self._handle_incoming_message(message))
            )

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


class ClientListenRawZCLCommand(WebSocketCommand):
    """Listen to raw ZCL data."""

    command: Literal[
        APICommands.CLIENT_LISTEN_RAW_ZCL
    ] = APICommands.CLIENT_LISTEN_RAW_ZCL


class ClientListenCommand(WebSocketCommand):
    """Listen for zhawss messages."""

    command: Literal[APICommands.CLIENT_LISTEN] = APICommands.CLIENT_LISTEN


class ClientDisconnectCommand(WebSocketCommand):
    """Disconnect this client."""

    command: Literal[APICommands.CLIENT_DISCONNECT] = APICommands.CLIENT_DISCONNECT


@decorators.websocket_command(ClientListenRawZCLCommand)
@decorators.async_response
async def listen_raw_zcl(
    server: Server, client: Client, message: WebSocketCommand
) -> None:
    """Listen for raw ZCL events."""
    client.receive_raw_zcl_events = True
    client.send_result_success(message)


@decorators.websocket_command(ClientListenCommand)
@decorators.async_response
async def listen(server: Server, client: Client, message: WebSocketCommand) -> None:
    """Listen for events."""
    client.receive_events = True
    client.send_result_success(message)


@decorators.websocket_command(ClientDisconnectCommand)
@decorators.async_response
async def disconnect(server: Server, client: Client, message: WebSocketCommand) -> None:
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
