"""Device Tracker platform for zhawss."""
from __future__ import annotations

import asyncio
import functools
import time
from typing import TYPE_CHECKING, Any

from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.platforms.sensor import Battery
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_POWER_CONFIGURATION

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

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
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the binary sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._battery_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_POWER_CONFIGURATION
        ]
        self._connected: bool = False
        self._keepalive_interval: int = 60
        self._should_poll: bool = True
        self._battery_level: int | None = None
        self._battery_cluster_handler.add_listener(self)
        self._cancel_refresh_handle = asyncio.create_task(self._refresh())

    async def async_update(self) -> None:
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
    async def _refresh(self) -> None:
        """Refresh the state of the device tracker."""
        await self.async_update()

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._connected

    def cluster_handler_attribute_updated(
        self, attr_id: int, attr_name: str, value: Any
    ) -> None:
        """Handle tracking."""
        if attr_name != "battery_percentage_remaining":
            return
        self.debug("battery_percentage_remaining updated: %s", value)
        self._connected = True
        self._battery_level = Battery.formatter(value)
        self.send_state_changed_event()

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device.
        Percentage from 0-100.
        """
        return self._battery_level

    def get_state(self) -> dict:
        return {
            "connected": self._connected,
            "battery_level": self._battery_level,
        }
