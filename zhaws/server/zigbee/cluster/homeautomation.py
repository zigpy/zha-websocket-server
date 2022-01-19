"""Home automation cluster handlers module for zhawss."""
from __future__ import annotations

import enum

from zigpy.zcl.clusters import homeautomation

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
    ClusterHandler,
)
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT,
    REPORT_CONFIG_DEFAULT,
    REPORT_CONFIG_OP,
)


@registries.CLUSTER_HANDLER_REGISTRY.register(
    homeautomation.ApplianceEventAlerts.cluster_id
)
class ApplianceEventAlerts(ClusterHandler):
    """Appliance Event Alerts cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(
    homeautomation.ApplianceIdentification.cluster_id
)
class ApplianceIdentification(ClusterHandler):
    """Appliance Identification cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(
    homeautomation.ApplianceStatistics.cluster_id
)
class ApplianceStatistics(ClusterHandler):
    """Appliance Statistics cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(homeautomation.Diagnostic.cluster_id)
class Diagnostic(ClusterHandler):
    """Diagnostic cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(
    homeautomation.ElectricalMeasurement.cluster_id
)
class ElectricalMeasurementClusterHandler(ClusterHandler):
    """Cluster handler that polls active power level."""

    HANDLER_NAME = CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT

    class MeasurementType(enum.IntFlag):
        """Measurement types."""

        ACTIVE_MEASUREMENT = 1
        REACTIVE_MEASUREMENT = 2
        APPARENT_MEASUREMENT = 4
        PHASE_A_MEASUREMENT = 8
        PHASE_B_MEASUREMENT = 16
        PHASE_C_MEASUREMENT = 32
        DC_MEASUREMENT = 64
        HARMONICS_MEASUREMENT = 128
        POWER_QUALITY_MEASUREMENT = 256

    REPORT_CONFIG = [
        {"attr": "active_power", "config": REPORT_CONFIG_OP},
        {"attr": "active_power_max", "config": REPORT_CONFIG_DEFAULT},
        {"attr": "apparent_power", "config": REPORT_CONFIG_OP},
        {"attr": "rms_current", "config": REPORT_CONFIG_OP},
        {"attr": "rms_current_max", "config": REPORT_CONFIG_DEFAULT},
        {"attr": "rms_voltage", "config": REPORT_CONFIG_OP},
        {"attr": "rms_voltage_max", "config": REPORT_CONFIG_DEFAULT},
    ]
    ZCL_INIT_ATTRS = {
        "ac_current_divisor": True,
        "ac_current_multiplier": True,
        "ac_power_divisor": True,
        "ac_power_multiplier": True,
        "ac_voltage_divisor": True,
        "ac_voltage_multiplier": True,
        "measurement_type": True,
        "power_divisor": True,
        "power_multiplier": True,
    }

    async def async_update(self) -> None:
        """Retrieve latest state."""
        self.debug("async_update")

        # This is a polling cluster handler. Don't allow cache.
        attrs = [
            a["attr"]
            for a in self.REPORT_CONFIG
            if a["attr"] not in self.cluster.unsupported_attributes
        ]
        result = await self.get_attributes(attrs, from_cache=False)
        if result:
            for attr, value in result.items():
                self.emit(
                    CLUSTER_HANDLER_EVENT,
                    ClusterAttributeUpdatedEvent(
                        id=self.cluster.attridx.get(attr, attr),
                        name=attr,
                        value=value,
                    ),
                )

    @property
    def ac_current_divisor(self) -> int:
        """Return ac current divisor."""
        return self.cluster.get("ac_current_divisor") or 1

    @property
    def ac_current_multiplier(self) -> int:
        """Return ac current multiplier."""
        return self.cluster.get("ac_current_multiplier") or 1

    @property
    def ac_voltage_divisor(self) -> int:
        """Return ac voltage divisor."""
        return self.cluster.get("ac_voltage_divisor") or 1

    @property
    def ac_voltage_multiplier(self) -> int:
        """Return ac voltage multiplier."""
        return self.cluster.get("ac_voltage_multiplier") or 1

    @property
    def ac_power_divisor(self) -> int:
        """Return active power divisor."""
        return self.cluster.get(
            "ac_power_divisor", self.cluster.get("power_divisor") or 1
        )

    @property
    def ac_power_multiplier(self) -> int:
        """Return active power divisor."""
        return self.cluster.get(
            "ac_power_multiplier", self.cluster.get("power_multiplier") or 1
        )

    @property
    def measurement_type(self) -> str | None:
        """Return Measurement type."""
        if (meas_type := self.cluster.get("measurement_type")) is None:
            return None

        meas_type = self.MeasurementType(meas_type)
        return ", ".join(m.name for m in self.MeasurementType if m in meas_type)  # type: ignore #TODO


@registries.CLUSTER_HANDLER_REGISTRY.register(
    homeautomation.MeterIdentification.cluster_id
)
class MeterIdentification(ClusterHandler):
    """Metering Identification cluster handler."""
