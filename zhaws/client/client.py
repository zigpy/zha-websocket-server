"""Client implementation for the zhaws.client."""
import asyncio
import logging
import pprint
from types import TracebackType
from typing import Any, Dict, Optional
import uuid

from aiohttp import ClientSession, ClientWebSocketResponse, client_exceptions
from aiohttp.http_websocket import WSMsgType

from zhaws.client.event import EventBase
from zhaws.client.model.messages import Message

SIZE_PARSE_JSON_EXECUTOR = 8192
_LOGGER = logging.getLogger(__package__)


class Client(EventBase):
    """Class to manage the IoT connection."""

    def __init__(
        self,
        ws_server_url: str,
        aiohttp_session: ClientSession,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Client class."""
        super().__init__(*args, **kwargs)
        self.ws_server_url = ws_server_url
        self.aiohttp_session = aiohttp_session
        # The WebSocket client
        self._client: Optional[ClientWebSocketResponse] = None
        self._loop = asyncio.get_running_loop()
        self._result_futures: Dict[str, asyncio.Future] = {}
        self._shutdown_complete_event: Optional[asyncio.Event] = None

    def __repr__(self) -> str:
        """Return the representation."""
        prefix = "" if self.connected else "not "
        return f"{type(self).__name__}(ws_server_url={self.ws_server_url!r}, {prefix}connected)"

    @property
    def connected(self) -> bool:
        """Return if we're currently connected."""
        return self._client is not None and not self._client.closed

    async def async_send_command(
        self,
        message: Dict[str, Any],
    ) -> dict:
        """Send a command and get a response."""
        future: "asyncio.Future[dict]" = self._loop.create_future()
        message_id = message["message_id"] = uuid.uuid4().int
        self._result_futures[message_id] = future
        await self._send_json_message(message)
        try:
            return await future
        finally:
            self._result_futures.pop(message_id)

    async def async_send_command_no_wait(self, message: Dict[str, Any]) -> None:
        """Send a command without waiting for the response."""
        message["messageId"] = uuid.uuid4().int
        await self._send_json_message(message)

    async def connect(self) -> None:
        """Connect to the websocket server."""

        _LOGGER.debug("Trying to connect")
        try:
            self._client = await self.aiohttp_session.ws_connect(
                self.ws_server_url,
                heartbeat=55,
                compress=15,
                max_msg_size=0,
            )
        except (
            client_exceptions.WSServerHandshakeError,
            client_exceptions.ClientError,
        ) as err:
            _LOGGER.error("Error connecting to server: %s", err)
            raise err

    async def listen(self) -> None:
        """Start listening to the websocket."""
        if not self.connected:
            raise Exception("Not connected when start listening")

        assert self._client

        try:
            while not self._client.closed:
                data = await self._receive_json_or_raise()

                self._handle_incoming_message(data)
        except Exception:
            pass

        finally:
            _LOGGER.debug("Listen completed. Cleaning up")

            for future in self._result_futures.values():
                future.cancel()
            self._result_futures.clear()

            if not self._client.closed:
                await self._client.close()

            if self._shutdown_complete_event:
                self._shutdown_complete_event.set()

    async def disconnect(self) -> None:
        """Disconnect the client."""
        _LOGGER.debug("Closing client connection")

        if not self.connected:
            return

        assert self._client

        self._shutdown_complete_event = asyncio.Event()
        await self._client.close()
        await self._shutdown_complete_event.wait()

        self._shutdown_complete_event = None

    async def _receive_json_or_raise(self) -> dict:
        """Receive json or raise."""
        assert self._client
        msg = await self._client.receive()

        if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
            raise Exception("Connection was closed.")

        if msg.type == WSMsgType.ERROR:
            raise Exception()

        if msg.type != WSMsgType.TEXT:
            raise Exception(f"Received non-Text message: {msg.type}")

        try:
            if len(msg.data) > SIZE_PARSE_JSON_EXECUTOR:
                data: dict = await self._loop.run_in_executor(None, msg.json)
            else:
                data = msg.json()
        except ValueError as err:
            raise Exception("Received invalid JSON.") from err

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Received message:\n%s\n", pprint.pformat(msg))

        return data

    def _handle_incoming_message(self, msg: dict) -> None:
        """Handle incoming message.

        Run all async tasks in a wrapper to log appropriately.
        """

        try:
            message = Message.parse_obj(msg).__root__
        except Exception as err:
            _LOGGER.error("Error parsing message: %s", err, exc_info=err)

        if message.message_type == "result":
            future = self._result_futures.get(message.message_id)

            if future is None:
                # no listener for this result
                return

            if message.success:
                future.set_result(message)
                return

            if msg["errorCode"] != "zwave_error":
                err = Exception(msg["messageId"], msg["errorCode"])
            else:
                err = Exception(
                    msg["messageId"], msg["zwaveErrorCode"], msg["zwaveErrorMessage"]
                )

            future.set_exception(err)
            return

        if message.message_type != "event":
            # Can't handle
            _LOGGER.debug(
                "Received message with unknown type '%s': %s",
                msg["message_type"],
                msg,
            )
            return
        try:
            self.emit(message.event_type, message)
        except Exception as err:
            _LOGGER.error("Error handling event: %s", err, exc_info=err)

    async def _send_json_message(self, message: Dict[str, Any]) -> None:
        """Send a message.

        Raises NotConnected if client not connected.
        """
        if not self.connected:
            raise Exception

        _LOGGER.warn("Publishing message:\n%s\n", pprint.pformat(message))

        assert self._client
        assert "message_id" in message

        await self._client.send_json(message)

    async def __aenter__(self) -> "Client":
        """Connect to the websocket."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the websocket."""
        await self.disconnect()
