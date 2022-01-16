"""Manufacturer specific cluster handlers module for zhawss."""
from typing import Any

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import ClusterHandler
from zhaws.server.zigbee.cluster.const import (
    REPORT_CONFIG_ASAP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
)


@registries.CLUSTER_HANDLER_REGISTRY.register(registries.SMARTTHINGS_HUMIDITY_CLUSTER)
class SmartThingsHumidity(ClusterHandler):
    """Smart Things Humidity cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 50),
        }
    ]


@registries.HANDLER_ONLY_CLUSTERS.register(0xFD00)
@registries.CLUSTER_HANDLER_REGISTRY.register(0xFD00)
class OsramButton(ClusterHandler):
    """Osram button cluster handler."""


@registries.HANDLER_ONLY_CLUSTERS.register(registries.PHILLIPS_REMOTE_CLUSTER)
@registries.CLUSTER_HANDLER_REGISTRY.register(registries.PHILLIPS_REMOTE_CLUSTER)
class PhillipsRemote(ClusterHandler):
    """Phillips remote cluster handler."""


@registries.HANDLER_ONLY_CLUSTERS.register(0xFCC0)
@registries.CLUSTER_HANDLER_REGISTRY.register(0xFCC0)
class OppleRemote(ClusterHandler):
    """Opple button cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(
    registries.SMARTTHINGS_ACCELERATION_CLUSTER
)
class SmartThingsAcceleration(ClusterHandler):
    """Smart Things Acceleration cluster handler."""

    REPORT_CONFIG = [
        {"attr": "acceleration", "config": REPORT_CONFIG_ASAP},
        {"attr": "x_axis", "config": REPORT_CONFIG_ASAP},
        {"attr": "y_axis", "config": REPORT_CONFIG_ASAP},
        {"attr": "z_axis", "config": REPORT_CONFIG_ASAP},
    ]

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute updates on this cluster."""
        if attrid == self.value_attribute:
            """TODO
            self.send_event(
                f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}",
                attrid,
                self._cluster.attributes.get(attrid, [UNKNOWN])[0],
                value,
            )
            """
            return
        """ TODO
        self.zha_send_event(
            SIGNAL_ATTR_UPDATED,
            {
                ATTR_ATTRIBUTE_ID: attrid,
                ATTR_ATTRIBUTE_NAME: self._cluster.attributes.get(attrid, [UNKNOWN])[0],
                ATTR_VALUE: value,
            },
        )
        """
        pass
