"""Controller implementation for the zhaws.client."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

from aiohttp import ClientSession
from async_timeout import timeout

from zhaws.client.client import Client
from zhaws.client.device import Device
from zhaws.client.group import Group
from zhaws.client.helpers import (
    AlarmControlPanelHelper,
    ButtonHelper,
    ClientHelper,
    ClimateHelper,
    CoverHelper,
    DeviceHelper,
    FanHelper,
    GroupHelper,
    LightHelper,
    LockHelper,
    NetworkHelper,
    NumberHelper,
    PlatformEntityHelper,
    SelectHelper,
    ServerHelper,
    SirenHelper,
    SwitchHelper,
)
from zhaws.client.model.commands import Command, CommandResponse
from zhaws.client.model.events import (
    DeviceConfiguredEvent,
    DeviceFullyInitializedEvent,
    DeviceJoinedEvent,
    DeviceLeftEvent,
    DeviceRemovedEvent,
    PlatformEntityEvent,
    RawDeviceInitializedEvent,
)
from zhaws.event import EventBase

CONNECT_TIMEOUT = 10

_LOGGER = logging.getLogger(__name__)


class Controller(EventBase):
    """Controller implementation."""

    def __init__(
        self, ws_server_url: str, aiohttp_session: ClientSession | None = None
    ):
        super().__init__()
        self._ws_server_url: str = ws_server_url
        self._client: Client = Client(ws_server_url, aiohttp_session)
        self._devices: dict[str, Device] = {}
        self._groups: dict[int, Group] = {}
        self._client.on_event(
            "platform_entity_event", self.handle_platform_entity_event
        )
        self._client.on_event("controller_event", self._handle_event_protocol)
        self.lights: LightHelper = LightHelper(self._client)
        self.switches: SwitchHelper = SwitchHelper(self._client)
        self.sirens: SirenHelper = SirenHelper(self._client)
        self.buttons: ButtonHelper = ButtonHelper(self._client)
        self.covers: CoverHelper = CoverHelper(self._client)
        self.fans: FanHelper = FanHelper(self._client)
        self.locks: LockHelper = LockHelper(self._client)
        self.numbers: NumberHelper = NumberHelper(self._client)
        self.selects: SelectHelper = SelectHelper(self._client)
        self.thermostats: ClimateHelper = ClimateHelper(self._client)
        self.alarm_control_panels: AlarmControlPanelHelper = AlarmControlPanelHelper(
            self._client
        )
        self.entities: PlatformEntityHelper = PlatformEntityHelper(self._client)
        self.clients: ClientHelper = ClientHelper(self._client)
        self.groups_helper: GroupHelper = GroupHelper(self._client)
        self.devices_helper: DeviceHelper = DeviceHelper(self._client)
        self.network: NetworkHelper = NetworkHelper(self._client)
        self.server_helper: ServerHelper = ServerHelper(self._client)

    @property
    def devices(self) -> dict[str, Device]:
        """Return the devices."""
        return self._devices

    @property
    def groups(self) -> dict[int, Group]:
        """Return the groups."""
        return self._groups

    async def connect(self) -> None:
        """Connect to the websocket server."""
        try:
            async with timeout(CONNECT_TIMEOUT):
                await self._client.connect()
        except Exception as err:
            _LOGGER.error("Unable to connect to the ZHA wss: %s", err)
            raise err

        await self._client.listen()

    async def disconnect(self) -> None:
        """Disconnect from the websocket server."""
        await self._client.disconnect()

    async def __aenter__(self) -> Controller:
        """Connect to the websocket server."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the websocket server."""
        await self.disconnect()

    async def send_command(self, command: Command) -> CommandResponse:
        """Send a command and get a response."""
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def load_devices(self) -> None:
        """Load devices from the websocket server."""
        response_devices = await self.devices_helper.get_devices()
        for ieee, device in response_devices.items():
            self._devices[ieee] = Device(device, self, self._client)

    async def load_groups(self) -> None:
        """Load groups from the websocket server."""
        response_groups = await self.groups_helper.get_groups()
        for id, group in response_groups.items():
            self._groups[id] = Group(group, self, self._client)

    def handle_platform_entity_event(self, event: PlatformEntityEvent) -> None:
        """Handle a platform_entity_event from the websocket server."""
        _LOGGER.debug("platform_entity_event: %s", event)
        if event.device:
            device = self.devices.get(event.device.ieee)
            if device is None:
                _LOGGER.warning("Received event from unknown device: %s", event)
                return
            entity: Any = device.device.entities.get(event.platform_entity.unique_id)
        elif event.group:
            group = self.groups.get(event.group.id)
            if not group:
                _LOGGER.warning("Received event from unknown group: %s", event)
                return
            entity = group.group.entities.get(event.platform_entity.unique_id)
        if entity is None:
            _LOGGER.warning("Received event for an unknown entity: %s", event)
            return
        entity.state = event.state  # update our state locally and emit an event
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
        # TODO devise a way to update existing devices so we don't lose event subscriptions
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

    def handle_group_member_removed(self, event: Any) -> None:
        """Handle group member removed event."""
        self.emit("group_member_removed", event)

    def handle_group_member_added(self, event: Any) -> None:
        """Handle group member added event."""
        self.emit("group_member_added", event)

    def handle_group_added(self, event: Any) -> None:
        """Handle group added event."""
        self.emit("group_added", event)

    def handle_group_removed(self, event: Any) -> None:
        """Handle group removed event."""
        self.emit("group_removed", event)
