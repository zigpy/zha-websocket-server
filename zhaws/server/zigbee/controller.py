"""Controller for zha web socket server."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Optional, Union

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
from zhaquirks import setup as setup_quirks
from zigpy.endpoint import Endpoint
from zigpy.group import Group as ZigpyGroup
from zigpy.types.named import EUI64
from zigpy.typing import DeviceType as ZigpyDeviceType

from zhaws.backports.enum import StrEnum
from zhaws.server.const import (
    CONF_ENABLE_QUIRKS,
    CONF_RADIO_TYPE,
    DEVICE,
    EVENT,
    EVENT_TYPE,
    IEEE,
    MESSAGE_TYPE,
    NWK,
    PAIRING_STATUS,
    ControllerEvents,
    EventTypes,
    MessageTypes,
)
from zhaws.server.platforms import discovery
from zhaws.server.zigbee.group import Group, GroupMemberReference

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server

from zhaws.server.zigbee.device import Device, DeviceStatus
from zhaws.server.zigbee.radio import RadioType

_LOGGER = logging.getLogger(__name__)


class DevicePairingStatus(StrEnum):
    """Status of a device."""

    PAIRED = "paired"
    INTERVIEW_COMPLETE = "interview_complete"
    CONFIGURED = "configured"
    INITIALIZED = "initialized"


class Controller:
    """Controller for the Zigbee application."""

    def __init__(self, server: Server):
        """Initialize the controller."""
        self._application_controller: ControllerApplication | None = None
        self._server: Server = server
        self.radio_description: Optional[str] = None
        self._devices: dict[EUI64, Device] = {}
        self._groups: dict[int, Group] = {}

    @property
    def is_running(self) -> bool:
        """Return true if the controller is running."""
        return self._application_controller is not None

    @property
    def server(self) -> Server:
        """Return the server."""
        return self._server

    @property
    def application_controller(self) -> ControllerApplication:
        """Return the Zigpy ControllerApplication"""
        return self._application_controller

    @property
    def coordinator_device(self) -> Device:
        """Get the coordinator device."""
        return self._devices[self._application_controller.ieee]

    @property
    def devices(self) -> dict[EUI64, Device]:
        """Get devices."""
        return self._devices

    @property
    def groups(self) -> dict[int, Group]:
        """Get groups."""
        return self._groups

    async def start_network(self, configuration: dict) -> None:
        """Start the Zigbee network."""
        if configuration.get(CONF_ENABLE_QUIRKS):
            setup_quirks(configuration)
        radio_type = configuration[CONF_RADIO_TYPE]
        app_controller_cls = RadioType[radio_type].controller
        self.radio_description = RadioType[radio_type].description
        controller_config = app_controller_cls.SCHEMA(configuration)  # type: ignore
        try:
            self._application_controller = await app_controller_cls.new(  # type: ignore
                controller_config, auto_form=True, start_radio=True
            )
        except (asyncio.TimeoutError, SerialException, OSError) as exc:
            _LOGGER.error(
                "Couldn't start %s coordinator",
                self.radio_description,
                exc_info=exc,
            )
            raise
        self.load_devices()
        self.load_groups()
        self.application_controller.add_listener(self)
        self.application_controller.groups.add_listener(self)

    def load_devices(self) -> None:
        """Load devices."""
        self._devices = {
            zigpy_device.ieee: Device(zigpy_device, self)
            for zigpy_device in self._application_controller.devices.values()
        }
        self.create_platform_entities()

    def load_groups(self) -> None:
        """Load groups."""
        for group_id, group in self.application_controller.groups.items():
            _LOGGER.info("Loading group with id: 0x%04x", group_id)
            group = Group(group, self._server)
            self._groups[group_id] = group
            # we can do this here because the entities are in the entity registry tied to the devices
            discovery.GROUP_PROBE.discover_group_entities(group)

    def create_platform_entities(self) -> None:
        """Create platform entities."""

        for platform in discovery.PLATFORMS:
            for platform_entity_class, args in self.server.data[platform]:
                platform_entity = platform_entity_class.create_platform_entity(*args)
                if platform_entity:
                    _LOGGER.debug("Platform entity data: %s", platform_entity.to_json())
            self.server.data[platform].clear()

    async def stop_network(self) -> None:
        """Stop the Zigbee network."""
        if self._application_controller is None:
            return

        await self._application_controller.pre_shutdown()
        self._application_controller = None

    def get_device(self, ieee: Union[EUI64, str]) -> Device:
        """Get a device by ieee address."""
        if isinstance(ieee, str):
            ieee = EUI64.convert(ieee)
        device = self._devices.get(ieee)
        if not device:
            raise ValueError(f"Device {str(ieee)} not found")
        return device

    def get_group(self, group_id: int) -> Group:
        """Get a group by group id."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError(f"Group {str(group_id)} not found")
        return group

    def device_joined(self, device: ZigpyDeviceType) -> None:
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """
        _LOGGER.info("Device %s - %s joined", device.ieee, f"0x{device.nwk:04x}")
        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_JOINED,
                IEEE: str(device.ieee),
                NWK: f"0x{device.nwk:04x}",
                PAIRING_STATUS: DevicePairingStatus.PAIRED,
            }
        )

    def raw_device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle a device initialization without quirks loaded."""
        _LOGGER.info(
            "Device %s - %s raw device initialized", device.ieee, f"0x{device.nwk:04x}"
        )

        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.RAW_DEVICE_INITIALIZED,
                IEEE: str(device.ieee),
                NWK: f"0x{device.nwk:04x}",
                PAIRING_STATUS: DevicePairingStatus.INTERVIEW_COMPLETE,
                "model": device.model if device.model else "unknown_model",
                "manufacturer": device.manufacturer
                if device.manufacturer
                else "unknown_manufacturer",
                "signature": device.get_signature(),
            }
        )

    def device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle device joined and basic information discovered."""
        _LOGGER.info("Device %s - %s initialized", device.ieee, f"0x{device.nwk:04x}")
        asyncio.create_task(self.async_device_initialized(device))

    def device_left(self, device: ZigpyDeviceType) -> None:
        """Handle device leaving the network."""
        _LOGGER.info("Device %s - %s left", device.ieee, f"0x{device.nwk:04x}")
        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_LEFT,
                IEEE: str(device.ieee),
                NWK: f"0x{device.nwk:04x}",
            }
        )

    def device_removed(self, device: ZigpyDeviceType) -> None:
        """Handle device being removed from the network."""
        device = self._devices.pop(device.ieee, None)
        if device is not None:
            message: dict[str, Any] = {DEVICE: device.zha_device_info}
            message[MESSAGE_TYPE] = MessageTypes.EVENT
            message[EVENT_TYPE] = EventTypes.CONTROLLER_EVENT
            message[EVENT] = ControllerEvents.DEVICE_REMOVED
            self.server.client_manager.broadcast(message)

    def group_member_removed(self, zigpy_group: ZigpyGroup, endpoint: Endpoint) -> None:
        """Handle zigpy group member removed event."""
        # need to handle endpoint correctly on groups
        group = self.get_or_create_group(zigpy_group)
        group.info("group_member_removed - endpoint: %s", endpoint)
        self._emit_group_event(group, ControllerEvents.GROUP_MEMBER_REMOVED)

    def group_member_added(self, zigpy_group: ZigpyGroup, endpoint: Endpoint) -> None:
        """Handle zigpy group member added event."""
        # need to handle endpoint correctly on groups
        group = self.get_or_create_group(zigpy_group)
        group.info("group_member_added - endpoint: %s", endpoint)
        self._emit_group_event(group, ControllerEvents.GROUP_MEMBER_ADDED)
        if len(group.members) > 1:
            # we need to do this because there wasn't already a group entity to remove and re-add
            discovery.GROUP_PROBE.discover_group_entities(group)

    def group_added(self, zigpy_group: ZigpyGroup) -> None:
        """Handle zigpy group added event."""
        group = self.get_or_create_group(zigpy_group)
        group.info("group_added")
        self._emit_group_event(group, ControllerEvents.GROUP_ADDED)

    def group_removed(self, zigpy_group: ZigpyGroup) -> None:
        """Handle zigpy group removed event."""
        # TODO handle entity change unsubs and sub for new events
        group = self._groups.pop(zigpy_group.group_id, None)
        if group is not None:
            group.info("group_removed")
            self._emit_group_event(group, ControllerEvents.GROUP_REMOVED)

    async def async_device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle device joined and basic information discovered (async)."""
        zha_device = self.get_or_create_device(device)
        # This is an active device so set a last seen if it is none
        if zha_device.last_seen is None:
            zha_device.async_update_last_seen(time.time())
        _LOGGER.debug(
            "device - %s:%s entering async_device_initialized - is_new_join: %s",
            f"0x{device.nwk:04x}",
            device.ieee,
            zha_device.status is not DeviceStatus.INITIALIZED,
        )

        if zha_device.status is DeviceStatus.INITIALIZED:
            # ZHA already has an initialized device so either the device was assigned a
            # new nwk or device was physically reset and added again without being removed
            _LOGGER.debug(
                "device - %s:%s has been reset and re-added or its nwk address changed",
                f"0x{device.nwk:04x}",
                device.ieee,
            )
            await self._async_device_rejoined(zha_device)
        else:
            _LOGGER.debug(
                "device - %s:%s has joined the ZHA zigbee network",
                f"0x{device.nwk:04x}",
                device.ieee,
            )
            await self._async_device_joined(zha_device)

        message: dict[str, Any] = {DEVICE: zha_device.zha_device_info}
        message[PAIRING_STATUS] = DevicePairingStatus.INITIALIZED
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        message[EVENT_TYPE] = EventTypes.CONTROLLER_EVENT
        message[EVENT] = ControllerEvents.DEVICE_FULLY_INITIALIZED
        self.server.client_manager.broadcast(message)

    def get_or_create_device(self, zigpy_device: ZigpyDeviceType) -> Device:
        """Get or create a device."""
        if (device := self._devices.get(zigpy_device.ieee)) is None:
            device = Device(zigpy_device, self)
            self._devices[zigpy_device.ieee] = device
        return device

    def get_or_create_group(self, zigpy_group: ZigpyGroup) -> Group:
        """Get or create a group."""
        group = self._groups.get(zigpy_group.group_id)
        if group is None:
            group = Group(zigpy_group, self.server)
            self._groups[zigpy_group.group_id] = group
        return group

    async def _async_device_joined(self, device: Device) -> None:
        device.available = True
        message: dict[str, Any] = {DEVICE: device.device_info}
        await device.async_configure()
        message[PAIRING_STATUS] = DevicePairingStatus.CONFIGURED
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        message[EVENT_TYPE] = EventTypes.CONTROLLER_EVENT
        message[EVENT] = ControllerEvents.DEVICE_CONFIGURED
        self.server.client_manager.broadcast(message)
        await device.async_initialize(from_cache=False)
        self.create_platform_entities()

    async def _async_device_rejoined(self, device: Device) -> None:
        _LOGGER.debug(
            "skipping discovery for previously discovered device - %s:%s",
            f"0x{device.nwk:04x}",
            device.ieee,
        )
        # we don't have to do this on a nwk swap but we don't have a way to tell currently
        await device.async_configure()
        message: dict[str, Any] = {DEVICE: device.device_info}
        message[PAIRING_STATUS] = DevicePairingStatus.CONFIGURED
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        message[EVENT_TYPE] = EventTypes.CONTROLLER_EVENT
        message[EVENT] = ControllerEvents.DEVICE_CONFIGURED
        self.server.client_manager.broadcast(message)
        # force async_initialize() to fire so don't explicitly call it
        device.available = False
        device.update_available(True)

    def get_group_by_name(self, group_name: str) -> Group | None:
        """Get ZHA group by name."""
        for group in self._groups.values():
            if group.name == group_name:
                return group
        return None

    async def async_create_zigpy_group(
        self,
        name: str,
        members: list[GroupMemberReference],
        group_id: int | None = None,
    ) -> Group:
        """Create a new Zigpy Zigbee group."""
        # we start with two to fill any gaps from a user removing existing groups

        if group_id is None:
            group_id = 2
            while group_id in self._groups:
                group_id += 1

        # guard against group already existing
        if self.get_group_by_name(name) is None:
            self.application_controller.groups.add_group(group_id, name)
            if members is not None:
                tasks = []
                for member in members:
                    _LOGGER.debug(
                        "Adding member with IEEE: %s and endpoint ID: %s to group: %s:0x%04x",
                        member.ieee,
                        member.endpoint_id,
                        name,
                        group_id,
                    )
                    tasks.append(
                        self.devices[member.ieee].async_add_endpoint_to_group(
                            member.endpoint_id, group_id
                        )
                    )
                await asyncio.gather(*tasks)
        return self._groups[group_id]

    async def async_remove_zigpy_group(self, group_id: int) -> None:
        """Remove a Zigbee group from Zigpy."""
        if not (group := self._groups.get(group_id)):
            _LOGGER.debug("Group: 0x%04x could not be found", group_id)
            return
        if group.members:
            tasks = []
            for member in group.members:
                tasks.append(member.async_remove_from_group())
            if tasks:
                await asyncio.gather(*tasks)
        self.application_controller.groups.pop(group_id)

    def _emit_group_event(self, group: Group, event: str) -> None:
        """Emit group event."""
        message: dict[str, Any] = {"group": group.to_json()}
        message[MESSAGE_TYPE] = MessageTypes.EVENT
        message[EVENT_TYPE] = EventTypes.CONTROLLER_EVENT
        message[EVENT] = event
        self.server.client_manager.broadcast(message)
