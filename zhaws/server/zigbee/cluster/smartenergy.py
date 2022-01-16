"""Smart energy cluster handlers module for zhawss."""
from __future__ import annotations

import enum
from functools import partialmethod
from typing import TYPE_CHECKING

from zigpy.zcl import Cluster as ZigpyClusterType
from zigpy.zcl.clusters import smartenergy

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import ClusterHandler
from zhaws.server.zigbee.cluster.const import (
    REPORT_CONFIG_ASAP,
    REPORT_CONFIG_DEFAULT,
    REPORT_CONFIG_OP,
)

if TYPE_CHECKING:
    from zhaws.server.zigbee.endpoint import Endpoint


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Calendar.cluster_id)
class Calendar(ClusterHandler):
    """Calendar cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.DeviceManagement.cluster_id)
class DeviceManagement(ClusterHandler):
    """Device Management cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Drlc.cluster_id)
class Drlc(ClusterHandler):
    """Demand Response and Load Control cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.EnergyManagement.cluster_id)
class EnergyManagement(ClusterHandler):
    """Energy Management cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Events.cluster_id)
class Events(ClusterHandler):
    """Event cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.KeyEstablishment.cluster_id)
class KeyEstablishment(ClusterHandler):
    """Key Establishment cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.MduPairing.cluster_id)
class MduPairing(ClusterHandler):
    """Pairing cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Messaging.cluster_id)
class Messaging(ClusterHandler):
    """Messaging cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Metering.cluster_id)
class Metering(ClusterHandler):
    """Metering cluster handler."""

    REPORT_CONFIG = [
        {"attr": "instantaneous_demand", "config": REPORT_CONFIG_OP},
        {"attr": "current_summ_delivered", "config": REPORT_CONFIG_DEFAULT},
        {"attr": "status", "config": REPORT_CONFIG_ASAP},
    ]

    ZCL_INIT_ATTRS = {
        "demand_formatting": True,
        "divisor": True,
        "metering_device_type": True,
        "multiplier": True,
        "summa_formatting": True,
        "unit_of_measure": True,
    }

    metering_device_type = {
        0: "Electric Metering",
        1: "Gas Metering",
        2: "Water Metering",
        3: "Thermal Metering",
        4: "Pressure Metering",
        5: "Heat Metering",
        6: "Cooling Metering",
        128: "Mirrored Gas Metering",
        129: "Mirrored Water Metering",
        130: "Mirrored Thermal Metering",
        131: "Mirrored Pressure Metering",
        132: "Mirrored Heat Metering",
        133: "Mirrored Cooling Metering",
    }

    class DeviceStatusElectric(enum.IntFlag):
        """Metering Device Status."""

        NO_ALARMS = 0
        CHECK_METER = 1
        LOW_BATTERY = 2
        TAMPER_DETECT = 4
        POWER_FAILURE = 8
        POWER_QUALITY = 16
        LEAK_DETECT = 32  # Really?
        SERVICE_DISCONNECT = 64
        RESERVED = 128

    class DeviceStatusDefault(enum.IntFlag):
        """Metering Device Status."""

        NO_ALARMS = 0

    class FormatSelector(enum.IntEnum):
        """Format specified selector."""

        DEMAND = 0
        SUMMATION = 1

    def __init__(self, cluster: ZigpyClusterType, endpoint: Endpoint) -> None:
        """Initialize Metering."""
        super().__init__(cluster, endpoint)
        self._format_spec: str | None = None
        self._summa_format: str | None = None

    @property
    def divisor(self) -> int:
        """Return divisor for the value."""
        return self.cluster.get("divisor") or 1

    @property
    def device_type(self) -> str | int | None:
        """Return metering device type."""
        dev_type = self.cluster.get("metering_device_type")
        if dev_type is None:
            return None
        return self.metering_device_type.get(dev_type, dev_type)

    @property
    def multiplier(self) -> int:
        """Return multiplier for the value."""
        return self.cluster.get("multiplier") or 1

    @property
    def metering_status(self) -> int | None:
        """Return metering device status."""
        if (status := self.cluster.get("status")) is None:
            return None
        if self.cluster.get("metering_device_type") == 0:
            # Electric metering device type
            return self.DeviceStatusElectric(status)
        return self.DeviceStatusDefault(status)

    @property
    def unit_of_measurement(self) -> str | int:
        """Return unit of measurement."""
        return self.cluster.get("unit_of_measure")

    async def async_initialize_handler_specific(self, from_cache: bool) -> None:
        """Fetch config from device and updates format specifier."""

        fmting = self.cluster.get(
            "demand_formatting", 0xF9
        )  # 1 digit to the right, 15 digits to the left
        self._format_spec = self.get_formatting(fmting)

        fmting = self.cluster.get(
            "summa_formatting", 0xF9
        )  # 1 digit to the right, 15 digits to the left
        self._summa_format = self.get_formatting(fmting)

    @staticmethod
    def get_formatting(formatting: int) -> str:
        """Return a formatting string, given the formatting value.

        Bits 0 to 2: Number of Digits to the right of the Decimal Point.
        Bits 3 to 6: Number of Digits to the left of the Decimal Point.
        Bit 7: If set, suppress leading zeros.
        """
        r_digits = int(formatting & 0x07)  # digits to the right of decimal point
        l_digits = (formatting >> 3) & 0x0F  # digits to the left of decimal point
        if l_digits == 0:
            l_digits = 15
        width = r_digits + l_digits + (1 if r_digits > 0 else 0)

        if formatting & 0x80:
            # suppress leading 0
            return f"{{:{width}.{r_digits}f}}"

        return f"{{:0{width}.{r_digits}f}}"

    def _formatter_function(
        self, selector: FormatSelector, value: int
    ) -> int | float | str:
        """Return formatted value for display."""
        val = value * self.multiplier / self.divisor
        if self.unit_of_measurement == 0:
            # Zigbee spec power unit is kW, but we show the value in W
            value_watt = val * 1000
            if value_watt < 100:
                return round(value_watt, 1)
            return round(value_watt)
        if selector == self.FormatSelector.SUMMATION:
            return str(self._summa_format).format(val).lstrip()
        return str(self._format_spec).format(val).lstrip()

    demand_formatter = partialmethod(_formatter_function, FormatSelector.DEMAND)
    summa_formatter = partialmethod(_formatter_function, FormatSelector.SUMMATION)


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Prepayment.cluster_id)
class Prepayment(ClusterHandler):
    """Prepayment cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Price.cluster_id)
class Price(ClusterHandler):
    """Price cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(smartenergy.Tunneling.cluster_id)
class Tunneling(ClusterHandler):
    """Tunneling cluster handler."""
