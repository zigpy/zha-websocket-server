"""Device Tracker platform for zhawss."""

import functools
import time
from typing import Dict, List, Union

from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.platforms.sensor import Battery
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_POWER_CONFIGURATION
from zhaws.server.zigbee.cluster.types import ClusterHandlerType
from zhaws.server.zigbee.types import DeviceType, EndpointType

STRICT_MATCH = functools.partial(
    PLATFORM_ENTITIES.strict_match, Platform.DEVICE_TRACKER
)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_POWER_CONFIGURATION)
class DeviceTracker(PlatformEntity):
    """Representation of a zhawss device tracker."""

    PLATFORM = Platform.DEVICE_TRACKER

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the binary sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._battery_cluster_handler: ClusterHandlerType = self.cluster_handlers.get(
            CLUSTER_HANDLER_POWER_CONFIGURATION
        )
        self._connected = False
        self._keepalive_interval = 60
        self._should_poll = True
        self._battery_level = None
        self._battery_cluster_handler.add_listener(self)

    async def async_update(self):
        """Handle polling."""
        previous_state = self._connected
        if self.device.last_seen is None:
            self._connected = False
        else:
            difference = time.time() - self.device.last_seen
            if difference > self._keepalive_interval:
                self._connected = False
            else:
                self._connected = True
        if previous_state != self._connected:
            self.send_state_changed_event()

    @periodic((30, 45))
    async def _refresh(self):
        """Refresh the state of the device tracker."""
        await self.async_update()

    @property
    def is_connected(self):
        """Return true if the device is connected to the network."""
        return self._connected

    def cluster_handler_attribute_updated(self, attr_id, attr_name, value):
        """Handle tracking."""
        if attr_name != "battery_percentage_remaining":
            return
        self.debug("battery_percentage_remaining updated: %s", value)
        self._connected = True
        self._battery_level = Battery.formatter(value)
        self.send_state_changed_event()

    @property
    def battery_level(self):
        """Return the battery level of the device.
        Percentage from 0-100.
        """
        return self._battery_level

    def get_state(self) -> Union[str, Dict, None]:
        return self._connected
