"""Controller implementation for the zhaws.client."""

import asyncio
from asyncio.tasks import Task
import logging
from typing import Any, Optional

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
    FanHelper,
    GroupHelper,
    LightHelper,
    LockHelper,
    NumberHelper,
    PlatformEntityHelper,
    SelectHelper,
    SirenHelper,
    SwitchHelper,
)
from zhaws.client.model.commands import (
    Command,
    CommandResponse,
    GetDevicesResponse,
    GroupsResponse,
)
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

    def __init__(self, ws_server_url: str, aiohttp_session: ClientSession):
        super().__init__()
        self._ws_server_url: str = ws_server_url
        self._aiohttp_session: ClientSession = aiohttp_session
        self._client: Client = Client(ws_server_url, aiohttp_session)
        self._listen_task: Optional[Task] = None
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
        self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Listen for messages from the websocket server."""
        try:
            await self._client.listen()
        except Exception as err:
            _LOGGER.error("Unable to connect to the zhawss: %s", err)

    async def send_command(self, command: Command) -> CommandResponse:
        """Send a command and get a response."""
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def load_devices(self) -> None:
        """Load devices from the websocket server."""
        response: GetDevicesResponse = await self._client.async_send_command(  # type: ignore
            {"command": "get_devices"}
        )
        for ieee, device in response.devices.items():
            self._devices[ieee] = Device(device, self, self._client)

    async def load_groups(self) -> None:
        """Load groups from the websocket server."""
        response: GroupsResponse = await self.groups_helper.get_groups()
        for id, group in response.groups.items():
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
