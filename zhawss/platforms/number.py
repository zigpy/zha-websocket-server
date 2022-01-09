"""Number platform for zhawss."""

import functools
import logging
from typing import Dict, List, Union

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_ANALOG_OUTPUT
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.NUMBER)

_LOGGER = logging.getLogger(__name__)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ANALOG_OUTPUT)
class Number(PlatformEntity):
    """Representation of a zhawss number."""

    PLATFORM = Platform.LOCK

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the number."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._analog_output_cluster_handler: ClusterHandlerType = (
            self.cluster_handlers.get(CLUSTER_HANDLER_ANALOG_OUTPUT)
        )
        self._analog_output_cluster_handler.add_listener(self)

    @property
    def value(self):
        """Return the current value."""
        return self._analog_output_cluster_handler.present_value

    @property
    def min_value(self):
        """Return the minimum value."""
        min_present_value = self._analog_output_cluster_handler.min_present_value
        if min_present_value is not None:
            return min_present_value
        return 0

    @property
    def max_value(self):
        """Return the maximum value."""
        max_present_value = self._analog_output_cluster_handler.max_present_value
        if max_present_value is not None:
            return max_present_value
        return 1023

    @property
    def step(self):
        """Return the value step."""
        resolution = self._analog_output_cluster_handler.resolution
        if resolution is not None:
            return resolution
        return super().step

    @property
    def name(self):
        """Return the name of the number entity."""
        description = self._analog_output_cluster_handler.description
        if description is not None and len(description) > 0:
            return f"{super().name} {description}"
        return super().name

    def cluster_handler_attribute_updated(self, attr_id, attr_name, value):
        """Handle value update from cluster handler."""
        self.send_state_changed_event()

    async def async_set_value(self, value):
        """Update the current value from service."""
        num_value = float(value)
        if await self._analog_output_cluster_handler.async_set_present_value(num_value):
            self.send_state_changed_event()

    async def async_update(self):
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

    def get_state(self) -> Union[str, Dict, None]:
        return self.value
