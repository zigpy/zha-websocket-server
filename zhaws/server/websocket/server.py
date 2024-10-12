"""ZHAWSS websocket server."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable
import contextlib
import logging
from time import monotonic
from types import TracebackType
from typing import TYPE_CHECKING, Any, Final, Literal

import websockets

from zha.application.discovery import PLATFORMS
from zhaws.server.config.model import ServerConfiguration
from zhaws.server.const import APICommands
from zhaws.server.decorators import periodic
from zhaws.server.platforms.api import load_platform_entity_apis
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.api.model import WebSocketCommand
from zhaws.server.websocket.client import ClientManager
from zhaws.server.zigbee.api import load_api as load_zigbee_controller_api
from zhaws.server.zigbee.controller import Controller

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client

BLOCK_LOG_TIMEOUT: Final[int] = 60
_LOGGER = logging.getLogger(__name__)


class Server:
    """ZHAWSS server implementation."""

    def __init__(self, *, configuration: ServerConfiguration) -> None:
        """Initialize the server."""
        self._config = configuration
        self._ws_server: websockets.WebSocketServer | None = None
        self._controller: Controller = Controller(self)
        self._client_manager: ClientManager = ClientManager(self)
        self._stopped_event: asyncio.Event = asyncio.Event()
        self._tracked_tasks: list[asyncio.Task] = []
        self._tracked_completable_tasks: list[asyncio.Task] = []
        self.data: dict[Any, Any] = {}
        for platform in PLATFORMS:
            self.data.setdefault(platform, [])
        self._register_api_commands()
        self._register_api_commands()
        self._tracked_tasks.append(
            asyncio.create_task(
                self._cleanup_tracked_tasks(), name="server_cleanup_tracked_tasks"
            )
        )

    @property
    def is_serving(self) -> bool:
        """Return whether or not the websocket server is serving."""
        return self._ws_server is not None and self._ws_server.is_serving

    @property
    def controller(self) -> Controller:
        """Return the zigbee application controller."""
        return self._controller

    @property
    def client_manager(self) -> ClientManager:
        """Return the zigbee application controller."""
        return self._client_manager

    @property
    def config(self) -> ServerConfiguration:
        """Return the server configuration."""
        return self._config

    async def start_server(self) -> None:
        """Start the websocket server."""
        assert self._ws_server is None
        self._stopped_event.clear()
        self._ws_server = await websockets.serve(
            self.client_manager.add_client,
            self._config.host,
            self._config.port,
            logger=_LOGGER,
        )
        if self._config.network_auto_start:
            await self._controller.start_network()

    async def wait_closed(self) -> None:
        """Wait until the server is not running."""
        await self._stopped_event.wait()
        _LOGGER.info("Server stopped. Completing remaining tasks...")
        tasks = [t for t in self._tracked_tasks if not (t.done() or t.cancelled())]
        for task in tasks:
            _LOGGER.debug("Cancelling task: %s", task)
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks, return_exceptions=True)

        tasks = [
            t
            for t in self._tracked_completable_tasks
            if not (t.done() or t.cancelled())
        ]
        for task in tasks:
            _LOGGER.debug("Cancelling task: %s", task)
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks, return_exceptions=True)

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
        """Enter the context manager."""
        await self.start_server()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Exit the context manager."""
        await self.stop_server()
        await self.wait_closed()

    async def block_till_done(self) -> None:
        """Block until all pending work is done."""
        # To flush out any call_soon_threadsafe
        await asyncio.sleep(0.001)
        start_time: float | None = None

        while self._tracked_completable_tasks:
            pending = [
                task for task in self._tracked_completable_tasks if not task.done()
            ]
            self._tracked_completable_tasks.clear()
            if pending:
                await self._await_and_log_pending(pending)

                if start_time is None:
                    # Avoid calling monotonic() until we know
                    # we may need to start logging blocked tasks.
                    start_time = 0
                elif start_time == 0:
                    # If we have waited twice then we set the start
                    # time
                    start_time = monotonic()
                elif monotonic() - start_time > BLOCK_LOG_TIMEOUT:
                    # We have waited at least three loops and new tasks
                    # continue to block. At this point we start
                    # logging all waiting tasks.
                    for task in pending:
                        _LOGGER.debug("Waiting for task: %s", task)
            else:
                await asyncio.sleep(0.001)

    async def _await_and_log_pending(self, pending: Iterable[Awaitable[Any]]) -> None:
        """Await and log tasks that take a long time."""
        # pylint: disable=no-self-use
        wait_time = 0
        while pending:
            _, pending = await asyncio.wait(pending, timeout=BLOCK_LOG_TIMEOUT)
            if not pending:
                return
            wait_time += BLOCK_LOG_TIMEOUT
            for task in pending:
                _LOGGER.debug("Waited %s seconds for task: %s", wait_time, task)

    def track_task(self, task: asyncio.Task) -> None:
        """Create a tracked task."""
        self._tracked_completable_tasks.append(task)

    @periodic((10, 10))
    async def _cleanup_tracked_tasks(self) -> None:
        """Cleanup tracked tasks."""
        done_tasks: list[asyncio.Task] = [
            task for task in self._tracked_completable_tasks if task.done()
        ]
        for task in done_tasks:
            self._tracked_completable_tasks.remove(task)

    def _register_api_commands(self) -> None:
        """Load server API commands."""
        from zhaws.server.websocket.client import load_api as load_client_api

        register_api_command(self, stop_server)
        load_zigbee_controller_api(self)
        load_platform_entity_apis(self)
        load_client_api(self)


class StopServerCommand(WebSocketCommand):
    """Stop the server."""

    command: Literal[APICommands.STOP_SERVER] = APICommands.STOP_SERVER


@decorators.websocket_command(StopServerCommand)
@decorators.async_response
async def stop_server(
    server: Server, client: Client, command: WebSocketCommand
) -> None:
    """Stop the Zigbee network."""
    client.send_result_success(command)
    await server.stop_server()
