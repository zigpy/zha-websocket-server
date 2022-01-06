"""Controller for zha web socket server."""
import asyncio
import logging
from typing import Any, Awaitable, List

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
from zhaquirks import setup as setup_quirks
from zigpy.endpoint import Endpoint
from zigpy.group import Group
from zigpy.typing import DeviceType as ZigpyDeviceType

from zhawss.const import CONF_ENABLE_QUIRKS, CONF_RADIO_TYPE
from zhawss.platforms import discovery
from zhawss.websocket.types import ServerType
from zhawss.zigbee.device import Device
from zhawss.zigbee.radio import RadioType
from zhawss.zigbee.types import DeviceType

_LOGGER = logging.getLogger(__name__)


class Controller:
    """Controller for the Zigbee application."""

    def __init__(self, server: ServerType):
        """Initialize the controller."""
        self._application_controller: ControllerApplication = None
        self._server: ServerType = server
        self.radio_description: str = None
        self._devices: List[DeviceType] = []

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

    def load_devices(self) -> None:
        """Load devices."""
        self._devices = [
            Device(zigpy_device, self)
            for zigpy_device in self._application_controller.devices.values()
        ]
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

    def get_devices(self) -> list[Any]:
        """Get Zigbee devices."""
        # temporary to test response
        return [device.zha_device_info for device in self._devices]

    def get_groups(self):
        """Get Zigbee groups."""

    # TODO connect the following methods to the client manager broadcast somehow
    def device_joined(self, device: ZigpyDeviceType) -> None:
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """

    def raw_device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle a device initialization without quirks loaded."""

    def device_initialized(self, device: ZigpyDeviceType) -> None:
        """Handle device joined and basic information discovered."""

    def device_left(self, device: ZigpyDeviceType) -> None:
        """Handle device leaving the network."""

    def group_member_removed(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member removed event."""

    def group_member_added(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member added event."""

    def group_added(self, zigpy_group: Group) -> None:
        """Handle zigpy group added event."""

    def group_removed(self, zigpy_group: Group) -> None:
        """Handle zigpy group removed event."""
