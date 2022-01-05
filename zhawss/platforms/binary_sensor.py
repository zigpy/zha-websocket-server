"""Binary Sensor module for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import (
    CLUSTER_HANDLER_ACCELEROMETER,
    CLUSTER_HANDLER_BINARY_INPUT,
    CLUSTER_HANDLER_OCCUPANCY,
    CLUSTER_HANDLER_ON_OFF,
    CLUSTER_HANDLER_ZONE,
)

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.BINARY_SENSOR)
MULTI_MATCH = functools.partial(
    PLATFORM_ENTITIES.multipass_match, Platform.BINARY_SENSOR
)


class BinarySensor(PlatformEntity):
    """BinarySensor platform entity."""

    SENSOR_ATTR = None
    PLATFORM = Platform.BINARY_SENSOR

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
