"""Controller for zha web socket server."""
import asyncio
from enum import Enum
import logging
import time
from typing import Any, Awaitable, Dict

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
from zhaquirks import setup as setup_quirks
from zigpy.endpoint import Endpoint
from zigpy.group import Group
from zigpy.types.named import EUI64
from zigpy.typing import DeviceType as ZigpyDeviceType

from zhawss.const import CONF_ENABLE_QUIRKS, CONF_RADIO_TYPE
from zhawss.platforms import discovery
from zhawss.websocket.types import ServerType
from zhawss.zigbee.device import Device, DeviceStatus
from zhawss.zigbee.radio import RadioType

_LOGGER = logging.getLogger(__name__)


class DevicePairingStatus(Enum):
    """Status of a device."""

    PAIRED = 1
    INTERVIEW_COMPLETE = 2
    CONFIGURED = 3
    INITIALIZED = 4


class Controller:
    """Controller for the Zigbee application."""

    def __init__(self, server: ServerType):
        """Initialize the controller."""
        self._application_controller: ControllerApplication = None
        self._server: ServerType = server
        self.radio_description: str = None
        self._devices: Dict[EUI64, Device] = {}

    @property
    def is_running(self) -> bool:
        """Return true if the controller is running."""
        return (
            self._application_controller
            and self._application_controller.is_controller_running
        )

    @property
    def server(self) -> ServerType:
        """Return the server."""
        return self._server

    @property
    def application_controller(self) -> ControllerApplication:
        """Return the Zigpy ControllerApplication"""
        return self._application_controller

    async def start_network(self, configuration) -> Awaitable[None]:
        """Start the Zigbee network."""
        if configuration.get(CONF_ENABLE_QUIRKS):
            setup_quirks(configuration)
        radio_type = configuration[CONF_RADIO_TYPE]
        app_controller_cls = RadioType[radio_type].controller
        self.radio_description = RadioType[radio_type].description
        controller_config = app_controller_cls.SCHEMA(configuration)
        try:
            self._application_controller = await app_controller_cls.new(
                controller_config, auto_form=True, start_radio=True
            )
        except (asyncio.TimeoutError, SerialException, OSError) as exception:
            _LOGGER.error(
                "Couldn't start %s coordinator",
                self.radio_description,
                exc_info=exception,
            )
        self.load_devices()
        self.application_controller.add_listener(self)

    def load_devices(self) -> None:
        """Load devices."""
        self._devices = {
            zigpy_device.ieee: Device(zigpy_device, self)
            for zigpy_device in self._application_controller.devices.values()
        }
        self.create_platform_entities()

    def create_platform_entities(self) -> None:
        """Create platform entities."""

        for platform in discovery.PLATFORMS:
            for platform_entity_class, args in self.server.data[platform]:
                platform_entity = platform_entity_class.create_platform_entity(*args)
                if platform_entity:
                    _LOGGER.debug("Platform entity data: %s", platform_entity.to_json())
            self.server.data[platform].clear()

    async def stop_network(self) -> Awaitable[None]:
        """Stop the Zigbee network."""
        await self._application_controller.pre_shutdown()

    def get_devices(self) -> Dict[str, Any]:
        """Get Zigbee devices."""
        # temporary to test response
        return {
            str(ieee): device.zha_device_info for ieee, device in self._devices.items()
        }

    def get_groups(self):
        """Get Zigbee groups."""

    def device_joined(self, device: ZigpyDeviceType) -> None:
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """
        _LOGGER.info("Device %s - %s joined", device.ieee, f"0x{device.nwk:04x}")
        self.server.client_manager.broadcast(
            {
                "message_type": "event",
                "event_type": "controller_event",
                "event": "device_joined",
                "ieee": str(device.ieee),
                "nwk": f"0x{device.nwk:04x}",
                "pairing_status": DevicePairingStatus.PAIRED.name,
            }
        )

    def raw_device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle a device initialization without quirks loaded."""
        _LOGGER.info(
            "Device %s - %s raw device initialized", device.ieee, f"0x{device.nwk:04x}"
        )
        self.server.client_manager.broadcast(
            {
                "message_type": "event",
                "event_type": "controller_event",
                "event": "raw_device_initialized",
                "ieee": str(device.ieee),
                "nwk": f"0x{device.nwk:04x}",
                "pairing_status": DevicePairingStatus.INTERVIEW_COMPLETE.name,
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
                "message_type": "event",
                "event_type": "controller_event",
                "event": "device_left",
                "ieee": str(device.ieee),
                "nwk": f"0x{device.nwk:04x}",
            }
        )

    def device_removed(self, device: ZigpyDeviceType):
        """Handle device being removed from the network."""
        device = self._devices.pop(device.ieee, None)
        if device is not None:
            message = {"device": device.zha_device_info}
            message["message_type"] = "event"
            message["event_type"] = "controller_event"
            message["event"] = "device_removed"
            self.server.client_manager.broadcast(message)

    def group_member_removed(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member removed event."""

    def group_member_added(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member added event."""

    def group_added(self, zigpy_group: Group) -> None:
        """Handle zigpy group added event."""

    def group_removed(self, zigpy_group: Group) -> None:
        """Handle zigpy group removed event."""

    async def async_device_initialized(self, device: ZigpyDeviceType):
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

        message = {"device": zha_device.zha_device_info}
        message["pairing_status"] = DevicePairingStatus.INITIALIZED.name
        message["message_type"] = "event"
        message["event_type"] = "controller_event"
        message["event"] = "device_fully_initialized"
        message["device"] = zha_device.zha_device_info
        self.server.client_manager.broadcast(message)

    def get_or_create_device(self, zigpy_device: ZigpyDeviceType):
        """Get or create a device."""
        if (device := self._devices.get(zigpy_device.ieee)) is None:
            device = Device(zigpy_device, self)
            self._devices[zigpy_device.ieee] = device
        return device

    async def _async_device_joined(self, device: Device) -> None:
        device.available = True
        message = {"device": device.device_info}
        await device.async_configure()
        message["pairing_status"] = DevicePairingStatus.CONFIGURED.name
        message["message_type"] = "event"
        message["event_type"] = "controller_event"
        message["event"] = "device_configured"
        self.server.client_manager.broadcast(message)
        await device.async_initialize(from_cache=False)
        self.create_platform_entities()

    async def _async_device_rejoined(self, device: Device):
        _LOGGER.debug(
            "skipping discovery for previously discovered device - %s:%s",
            f"0x{device.nwk:04x}",
            device.ieee,
        )
        # we don't have to do this on a nwk swap but we don't have a way to tell currently
        await device.async_configure()
        message = {"device": device.device_info}
        message["pairing_status"] = DevicePairingStatus.CONFIGURED.name
        message["message_type"] = "event"
        message["event_type"] = "controller_event"
        message["event"] = "device_configured"
        self.server.client_manager.broadcast(message)
        # force async_initialize() to fire so don't explicitly call it
        device.available = False
        device.update_available(True)
