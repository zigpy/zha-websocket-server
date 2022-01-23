"""Number platform for zhawss."""
from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_ANALOG_OUTPUT

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.NUMBER)

_LOGGER = logging.getLogger(__name__)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ANALOG_OUTPUT)
class Number(PlatformEntity):
    """Representation of a zhawss number."""

    PLATFORM = Platform.LOCK

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the number."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._analog_output_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_ANALOG_OUTPUT
        ]
        self._analog_output_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def value(self) -> float:
        """Return the current value."""
        return self._analog_output_cluster_handler.present_value

    @property
    def min_value(self) -> float:
        """Return the minimum value."""
        min_present_value = self._analog_output_cluster_handler.min_present_value
        if min_present_value is not None:
            return min_present_value
        return 0

    @property
    def max_value(self) -> float:
        """Return the maximum value."""
        max_present_value = self._analog_output_cluster_handler.max_present_value
        if max_present_value is not None:
            return max_present_value
        return 1023

    @property
    def step(self) -> float | None:
        """Return the value step."""
        return self._analog_output_cluster_handler.resolution

    @property
    def name(self) -> str:
        """Return the name of the number entity."""
        description = self._analog_output_cluster_handler.description
        if description is not None and len(description) > 0:
            return f"{super().name} {description}"
        return super().name

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle value update from cluster handler."""
        self.maybe_send_state_changed_event()

    async def async_set_value(self, value: Any) -> None:
        """Update the current value from service."""
        num_value = float(value)
        if await self._analog_output_cluster_handler.async_set_present_value(num_value):
            self.maybe_send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve the state of the entity."""
        await super().async_update()
        _LOGGER.debug("polling current state")
        if self._analog_output_cluster_handler:
            value = await self._analog_output_cluster_handler.get_attribute_value(
                "present_value", from_cache=False
            )
            _LOGGER.debug("read value=%s", value)

    def to_json(self) -> dict:
        json = super().to_json()
        json["engineer_units"] = self._analog_output_cluster_handler.engineering_units
        json["application_type"] = self._analog_output_cluster_handler.application_type
        json["step"] = self.step
        json["min_value"] = self.min_value
        json["max_value"] = self.max_value
        json["name"] = self.name
        return json

    def get_state(self) -> dict:
        """Return the state of the entity."""
        response = super().get_state()
        response["state"] = self.value
        return response
