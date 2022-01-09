"""Controller implementation for the zhawssclient."""

import asyncio
from asyncio.tasks import Task
import logging
from typing import Awaitable, Optional

from aiohttp import ClientSession
from async_timeout import timeout

from zhawssclient.client import Client
from zhawssclient.event import EventBase
from zhawssclient.model.commands import GetDevicesResponse

CONNECT_TIMEOUT = 10

_LOGGER = logging.getLogger(__name__)


class Controller(EventBase):
    """Controller implementation."""

    def __init__(self, ws_server_url: str, aiohttp_session: ClientSession):
        self._ws_server_url: str = ws_server_url
        self._aiohttp_session: ClientSession = aiohttp_session
        self._client: Client = Client(ws_server_url, aiohttp_session)
        self._listen_task: Optional[Task] = None

    async def connect(self) -> Awaitable[None]:
        """Connect to the websocket server."""
        try:
            async with timeout(CONNECT_TIMEOUT):
                await self._client.connect()
        except Exception as err:
            _LOGGER.error("Unable to connect to the ZHA wss: %s", err)
            raise err
        self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> Awaitable[None]:
        """Listen for messages from the websocket server."""
        try:
            await self._client.listen()
        except Exception as err:
            _LOGGER.error("Unable to connect to the zhawss: %s", err)

    async def get_devices(self) -> Awaitable[GetDevicesResponse]:
        """Get devices from the websocket server."""
        data = await self._client.async_send_command({"command": "get_devices"})
        return GetDevicesResponse.parse_obj(data)
