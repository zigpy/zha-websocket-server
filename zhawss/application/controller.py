"""Controller for zha web socket server."""
import asyncio
from asyncio.futures import Future
import logging
from typing import Any, Dict

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
from zhaquirks import setup as setup_quirks
from zigpy.device import Device
from zigpy.endpoint import Endpoint
from zigpy.group import Group

from zhawss.const import CONF_ENABLE_QUIRKS, CONF_RADIO_TYPE
from zhawss.radio import RadioType
from zhawss.websocket_api.api import load_api

_LOGGER = logging.getLogger(__name__)


class Controller:
    """Controller for the Zigbee application."""

    def __init__(self, waiter: Future):
        """Initialize the controller."""
        self.application_controller: ControllerApplication = None
        self._waiter: Future = waiter
        self.radio_description: str = None
        self.data: Dict[str, Any] = {}
        load_api(self)

    async def start_network(self, configuration):
        """Start the Zigbee network."""
        if configuration.get(CONF_ENABLE_QUIRKS):
            setup_quirks(configuration)
        radio_type = configuration[CONF_RADIO_TYPE]
        app_controller_cls = RadioType[radio_type].controller
        self.radio_description = RadioType[radio_type].description
        controller_config = app_controller_cls.SCHEMA(configuration)
        try:
            self.application_controller = await app_controller_cls.new(
                controller_config, auto_form=True, start_radio=True
            )
        except (asyncio.TimeoutError, SerialException, OSError) as exception:
            _LOGGER.error(
                "Couldn't start %s coordinator",
                self.radio_description,
                exc_info=exception,
            )

    async def stop_network(self, _):
        """Stop the Zigbee network."""
        await self.application_controller.pre_shutdown()

    async def stop_server(self, _):
        """Stop the websocket server."""
        self._waiter.set_result(True)

    def get_devices(self) -> list[Device]:
        """Get Zigbee devices."""
        return list(self.application_controller.devices.values())

    def get_groups(self):
        """Get Zigbee groups."""

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
