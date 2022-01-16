"""Lighting cluster handlers module for zhawss."""
from __future__ import annotations

from contextlib import suppress

from zigpy.zcl.clusters import lighting

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import ClientClusterHandler, ClusterHandler
from zhaws.server.zigbee.cluster.const import REPORT_CONFIG_DEFAULT


@registries.CLUSTER_HANDLER_REGISTRY.register(lighting.Ballast.cluster_id)
class Ballast(ClusterHandler):
    """Ballast cluster handler."""


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(lighting.Color.cluster_id)
class ColorClientClusterHandler(ClientClusterHandler):
    """Color client cluster handler."""


@registries.BINDABLE_CLUSTERS.register(lighting.Color.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(lighting.Color.cluster_id)
class ColorClusterHandler(ClusterHandler):
    """Color cluster handler."""

    CAPABILITIES_COLOR_XY = 0x08
    CAPABILITIES_COLOR_TEMP = 0x10
    UNSUPPORTED_ATTRIBUTE = 0x86
    REPORT_CONFIG = [
        {"attr": "current_x", "config": REPORT_CONFIG_DEFAULT},
        {"attr": "current_y", "config": REPORT_CONFIG_DEFAULT},
        {"attr": "color_temperature", "config": REPORT_CONFIG_DEFAULT},
    ]
    MAX_MIREDS: int = 500
    MIN_MIREDS: int = 153
    ZCL_INIT_ATTRS = {
        "color_temp_physical_min": True,
        "color_temp_physical_max": True,
        "color_capabilities": True,
        "color_loop_active": False,
    }

    @property
    def color_capabilities(self) -> int:
        """Return color capabilities of the light."""
        with suppress(KeyError):
            return self.cluster["color_capabilities"]
        if self.cluster.get("color_temperature") is not None:
            return self.CAPABILITIES_COLOR_XY | self.CAPABILITIES_COLOR_TEMP
        return self.CAPABILITIES_COLOR_XY

    @property
    def color_loop_active(self) -> int | None:
        """Return cached value of the color_loop_active attribute."""
        return self.cluster.get("color_loop_active")

    @property
    def color_temperature(self) -> int | None:
        """Return cached value of color temperature."""
        return self.cluster.get("color_temperature")

    @property
    def current_x(self) -> int | None:
        """Return cached value of the current_x attribute."""
        return self.cluster.get("current_x")

    @property
    def current_y(self) -> int | None:
        """Return cached value of the current_y attribute."""
        return self.cluster.get("current_y")

    @property
    def min_mireds(self) -> int:
        """Return the coldest color_temp that this cluster handler supports."""
        return self.cluster.get("color_temp_physical_min", self.MIN_MIREDS)

    @property
    def max_mireds(self) -> int:
        """Return the warmest color_temp that this cluster handler supports."""
        return self.cluster.get("color_temp_physical_max", self.MAX_MIREDS)
