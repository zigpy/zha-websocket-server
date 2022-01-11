"""Controller implementation for the zhawssclient."""

import asyncio
from asyncio.tasks import Task
import logging
from typing import Awaitable, Dict, Optional

from aiohttp import ClientSession
from async_timeout import timeout

from zhawssclient.client import Client
from zhawssclient.device import Device
from zhawssclient.event import EventBase
from zhawssclient.model.commands import GetDevicesResponse
from zhawssclient.model.events import (
    DeviceConfiguredEvent,
    DeviceFullyInitializedEvent,
    DeviceJoinedEvent,
    DeviceLeftEvent,
    DeviceRemovedEvent,
    PlatformEntityEvent,
    RawDeviceInitializedEvent,
)

CONNECT_TIMEOUT = 10

_LOGGER = logging.getLogger(__name__)


class Controller(EventBase):
    """Controller implementation."""

    def __init__(self, ws_server_url: str, aiohttp_session: ClientSession):
        super().__init__()
        self._ws_server_url: str = ws_server_url
        self._aiohttp_session: ClientSession = aiohttp_session
        self._client: Client = Client(ws_server_url, aiohttp_session)
        self._listen_task: Optional[Task] = None
        self._devices: Dict[str, Device] = {}
        self._client.on("platform_entity_event", self.handle_platform_entity_event)
        self._client.on("controller_event", self._handle_event_protocol)

    @property
    def devices(self) -> Dict[str, Device]:
        """Return the devices."""
        return self._devices

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

    async def load_devices(self) -> Awaitable[None]:
        """Load devices from the websocket server."""
        response: GetDevicesResponse = await self._client.async_send_command(
            {"command": "get_devices"}
        )
        for ieee, device in response.devices.items():
            self._devices[ieee] = Device(device, self, self._client)

    def handle_platform_entity_event(self, event: PlatformEntityEvent) -> None:
        """Handle a platform_entity_event from the websocket server."""
        _LOGGER.debug("platform_entity_event: %s", event)
        device = self.devices.get(event.device.ieee)
        if device is None:
            _LOGGER.warning("Received event from unknown device: %s", event)
            return
        entity = device.device.entities.get(event.platform_entity.unique_id)
        if entity is None:
            _LOGGER.warning("Received event for an unknown entity: %s", event)
            return
        entity.emit(event.event, event)

    def handle_device_joined(self, event: DeviceJoinedEvent) -> None:
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """
        _LOGGER.info("Device %s - %s joined", event.ieee, event.nwk)
        self.emit("device_joined", event)

    def handle_raw_device_initialized(self, event: RawDeviceInitializedEvent) -> None:
        """Handle a device initialization without quirks loaded."""
        _LOGGER.info("Device %s - %s raw device initialized", event.ieee, event.nwk)
        self.emit("raw_device_initialized", event)

    def handle_device_configured(self, event: DeviceConfiguredEvent) -> None:
        """Handle device configured event."""
        device = event.device
        _LOGGER.info("Device %s - %s configured", device.ieee, device.nwk)
        self.emit("device_configured", event)

    def handle_device_fully_initialized(
        self, event: DeviceFullyInitializedEvent
    ) -> None:
        """Handle device joined and basic information discovered."""
        device = event.device
        _LOGGER.info("Device %s - %s initialized", device.ieee, device.nwk)
        self._devices[device.ieee] = Device(device, self, self._client)
        self.emit("device_fully_initialized", event)

    def handle_device_left(self, event: DeviceLeftEvent) -> None:
        """Handle device leaving the network."""
        _LOGGER.info("Device %s - %s left", event.ieee, event.nwk)
        self.emit("device_left", event)

    def handle_device_removed(self, event: DeviceRemovedEvent) -> None:
        """Handle device being removed from the network."""
        device = event.device
        _LOGGER.info(
            "Device %s - %s has been removed from the network", device.ieee, device.nwk
        )
        self._devices.pop(device.ieee, None)
        self.emit("device_removed", event)

    def handle_group_member_removed(self, event) -> None:
        """Handle group member removed event."""
        self.emit("group_member_removed", event)

    def handle_group_member_added(self, event) -> None:
        """Handle group member added event."""
        self.emit("group_member_added", event)

    def handle_group_added(self, event) -> None:
        """Handle group added event."""
        self.emit("group_added", event)

    def handle_group_removed(self, event) -> None:
        """Handle group removed event."""
        self.emit("group_removed", event)
