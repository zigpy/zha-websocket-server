"""Device Tracker platform for zhawss."""
from __future__ import annotations

import asyncio
import functools
import time
from typing import TYPE_CHECKING

from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.platforms.sensor import Battery
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
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
        self._battery_level: float | None = None
        self._battery_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )
        self._cancel_refresh_handle = asyncio.create_task(self._refresh())

    async def async_update(self) -> None:
        """Handle polling."""
        if self.device.last_seen is None:
            self._connected = False
        else:
            difference = time.time() - self.device.last_seen
            if difference > self._keepalive_interval:
                self._connected = False
            else:
                self._connected = True
        self.maybe_send_state_changed_event()

    @periodic((30, 45))
    async def _refresh(self) -> None:
        """Refresh the state of the device tracker."""
        await self.async_update()

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._connected

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle tracking."""
        if event.name != "battery_percentage_remaining":
            return
        self.debug("battery_percentage_remaining updated: %s", event.value)
        self._connected = True
        self._battery_level = Battery.formatter(event.value)
        self.maybe_send_state_changed_event()

    @property
    def battery_level(self) -> float | None:
        """Return the battery level of the device.
        Percentage from 0-100.
        """
        return self._battery_level

    def get_state(self) -> dict:
        """Return the state of the device."""
        response = super().get_state()
        response.update(
            {
                "connected": self._connected,
                "battery_level": self._battery_level,
            }
        )
        return response
