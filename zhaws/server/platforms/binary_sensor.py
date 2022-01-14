"""Binary Sensor module for zhawss."""

import functools
from typing import Dict, List, Union

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_ACCELEROMETER,
    CLUSTER_HANDLER_BINARY_INPUT,
    CLUSTER_HANDLER_OCCUPANCY,
    CLUSTER_HANDLER_ON_OFF,
    CLUSTER_HANDLER_ZONE,
)
from zhaws.server.zigbee.cluster.types import ClusterHandlerType
from zhaws.server.zigbee.types import DeviceType, EndpointType

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.BINARY_SENSOR)
MULTI_MATCH = functools.partial(
    PLATFORM_ENTITIES.multipass_match, Platform.BINARY_SENSOR
)


class BinarySensor(PlatformEntity):
    """BinarySensor platform entity."""

    SENSOR_ATTR = None
    PLATFORM = Platform.BINARY_SENSOR

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the binary sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandlerType = cluster_handlers[0]
        self._cluster_handler.add_listener(self)
        value = self._cluster_handler.cluster.get("zone_status")
        self._state: bool = value & 3 if value is not None else False

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        if self._state is None:
            return False
        return self._state

    def get_state(self) -> Union[str, Dict, None]:
        return self.is_on

    def cluster_handler_attribute_updated(self, attr_id, attr_name, value):
        """handle attribute updates from the cluster handler."""
        if self.SENSOR_ATTR is None or self.SENSOR_ATTR != attr_name:
            return
        self._state = bool(value)
        self.send_state_changed_event()

    async def async_update(self):
        """Attempt to retrieve on off state from the binary sensor."""
        await super().async_update()
        previous_state = self._state
        attribute = getattr(self._cluster_handler, "value_attribute", "on_off")
        attr_value = await self._cluster_handler.get_attribute_value(attribute)
        if attr_value is not None:
            self._state = attr_value
            if previous_state != self._state:
                self.send_state_changed_event()

    def to_json(self) -> dict:
        """Return a JSON representation of the binary sensor."""
        json = super().to_json()
        json["sensor_attribute"] = self.SENSOR_ATTR
        return json


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ACCELEROMETER)
class Accelerometer(BinarySensor):
    """ZHA BinarySensor."""

    SENSOR_ATTR = "acceleration"


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_OCCUPANCY)
class Occupancy(BinarySensor):
    """ZHA BinarySensor."""

    SENSOR_ATTR = "occupancy"


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ON_OFF)
class Opening(BinarySensor):
    """ZHA BinarySensor."""

    SENSOR_ATTR = "on_off"


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BINARY_INPUT)
class BinaryInput(BinarySensor):
    """ZHA BinarySensor."""

    SENSOR_ATTR = "present_value"


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    manufacturers="IKEA of Sweden",
    models=lambda model: isinstance(model, str)
    and model is not None
    and model.find("motion") != -1,
)
@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    manufacturers="Philips",
    models={"SML001", "SML002"},
)
class Motion(BinarySensor):
    """ZHA BinarySensor."""

    SENSOR_ATTR = "on_off"


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ZONE)
class IASZone(BinarySensor):
    """ZHA IAS BinarySensor."""

    SENSOR_ATTR = "zone_status"

    async def async_update(self):
        """Attempt to retrieve on off state from the binary sensor."""
        await super().async_update()
        previous_state = self._state
        value = await self._cluster_handler.get_attribute_value("zone_status")
        if value is not None:
            self._state = value & 3
            if previous_state != self._state:
                self.send_state_changed_event()

    def to_json(self) -> dict:
        """Return a JSON representation of the binary sensor."""
        json = super().to_json()
        json["zone_type"] = self._cluster_handler.cluster.get("zone_type")
        return json
