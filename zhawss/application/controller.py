"""Controller for zha web socket server."""
import asyncio
import logging

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
from zigpy.device import Device
from zigpy.endpoint import Endpoint
from zigpy.group import Group

_LOGGER = logging.getLogger(__name__)


class Controller:
    """Controller for the Zigbee application."""

    def __init__(self, websocket):
        """Initialize the controller."""
        self.application_controller: ControllerApplication = None
        self._websocket = websocket

    async def start_network(self, configuration):
        """Start the Zigbee network."""
        controller_config = ControllerApplication.SCHEMA(configuration)
        try:
            self.application_controller = await ControllerApplication.new(
                controller_config, auto_form=True, start_radio=True
            )
        except (asyncio.TimeoutError, SerialException, OSError) as exception:
            _LOGGER.error(
                "Couldn't start %s coordinator",
                "/dev/cu.GoControl_zigbee\u0011",
                exc_info=exception,
            )

    async def stop_network(self):
        """Stop the Zigbee network."""
        await self.application_controller.pre_shutdown()

    async def get_devices(self):
        """Stop the Zigbee network."""

    async def get_groups(self):
        """Stop the Zigbee network."""

    def device_joined(self, device: Device):
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """

    def raw_device_initialized(self, device: Device):
        """Handle a device initialization without quirks loaded."""

    def device_initialized(self, device: Device):
        """Handle device joined and basic information discovered."""

    def device_left(self, device: Device):
        """Handle device leaving the network."""

    def group_member_removed(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member removed event."""

    def group_member_added(self, zigpy_group: Group, endpoint: Endpoint) -> None:
        """Handle zigpy group member added event."""

    def group_added(self, zigpy_group: Group) -> None:
        """Handle zigpy group added event."""

    def group_removed(self, zigpy_group: Group) -> None:
        """Handle zigpy group removed event."""
