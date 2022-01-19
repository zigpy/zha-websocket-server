"""
HVAC cluster handlers module for zhawss.

For more details about this component, please refer to the documentation at
https://home-assistant.io/integrations/zha/
"""
from __future__ import annotations

from typing import Any

from zigpy.exceptions import ZigbeeException
from zigpy.zcl.clusters import hvac
from zigpy.zcl.foundation import Status

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
    ClusterHandler,
)
from zhaws.server.zigbee.cluster.const import (
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
    REPORT_CONFIG_OP,
)

REPORT_CONFIG_CLIMATE = (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 25)
REPORT_CONFIG_CLIMATE_DEMAND = (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 5)
REPORT_CONFIG_CLIMATE_DISCRETE = (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 1)


@registries.CLUSTER_HANDLER_REGISTRY.register(hvac.Dehumidification.cluster_id)
class Dehumidification(ClusterHandler):
    """Dehumidification cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(hvac.Fan.cluster_id)
class FanClusterHandler(ClusterHandler):
    """Fan cluster handler."""

    _value_attribute = 0

    REPORT_CONFIG = [{"attr": "fan_mode", "config": REPORT_CONFIG_OP}]
    ZCL_INIT_ATTRS = {"fan_mode_sequence": True}

    @property
    def fan_mode(self) -> int | None:
        """Return current fan mode."""
        return self.cluster.get("fan_mode")

    @property
    def fan_mode_sequence(self) -> int | None:
        """Return possible fan mode speeds."""
        return self.cluster.get("fan_mode_sequence")

    async def async_set_speed(self, value: Any) -> None:
        """Set the speed of the fan."""

        try:
            await self.cluster.write_attributes({"fan_mode": value})
        except ZigbeeException as ex:
            self.error("Could not set speed: %s", ex)
            return

    async def async_update(self) -> None:
        """Retrieve latest state."""
        await self.get_attribute_value("fan_mode", from_cache=False)

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute update from fan cluster."""
        attr_name = self.cluster.attributes.get(attrid, [attrid])[0]
        self.debug(
            "Attribute report '%s'[%s] = %s", self.cluster.name, attr_name, value
        )
        if attr_name == "fan_mode":
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=attrid,
                    name=attr_name,
                    value=value,
                ),
            )


@registries.CLUSTER_HANDLER_REGISTRY.register(hvac.Pump.cluster_id)
class Pump(ClusterHandler):
    """Pump cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(hvac.Thermostat.cluster_id)
class ThermostatClusterHandler(ClusterHandler):
    """Thermostat cluster handler."""

    REPORT_CONFIG = [
        {"attr": "local_temp", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "occupied_cooling_setpoint", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "occupied_heating_setpoint", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "unoccupied_cooling_setpoint", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "unoccupied_heating_setpoint", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "running_mode", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "running_state", "config": REPORT_CONFIG_CLIMATE_DEMAND},
        {"attr": "system_mode", "config": REPORT_CONFIG_CLIMATE},
        {"attr": "occupancy", "config": REPORT_CONFIG_CLIMATE_DISCRETE},
        {"attr": "pi_cooling_demand", "config": REPORT_CONFIG_CLIMATE_DEMAND},
        {"attr": "pi_heating_demand", "config": REPORT_CONFIG_CLIMATE_DEMAND},
    ]
    ZCL_INIT_ATTRS: dict[int | str, bool] = {
        "abs_min_heat_setpoint_limit": True,
        "abs_max_heat_setpoint_limit": True,
        "abs_min_cool_setpoint_limit": True,
        "abs_max_cool_setpoint_limit": True,
        "ctrl_seqe_of_oper": False,
        "max_cool_setpoint_limit": True,
        "max_heat_setpoint_limit": True,
        "min_cool_setpoint_limit": True,
        "min_heat_setpoint_limit": True,
    }

    @property
    def abs_max_cool_setpoint_limit(self) -> int:
        """Absolute maximum cooling setpoint."""
        return self.cluster.get("abs_max_cool_setpoint_limit", 3200)

    @property
    def abs_min_cool_setpoint_limit(self) -> int:
        """Absolute minimum cooling setpoint."""
        return self.cluster.get("abs_min_cool_setpoint_limit", 1600)

    @property
    def abs_max_heat_setpoint_limit(self) -> int:
        """Absolute maximum heating setpoint."""
        return self.cluster.get("abs_max_heat_setpoint_limit", 3000)

    @property
    def abs_min_heat_setpoint_limit(self) -> int:
        """Absolute minimum heating setpoint."""
        return self.cluster.get("abs_min_heat_setpoint_limit", 700)

    @property
    def ctrl_seqe_of_oper(self) -> int:
        """Control Sequence of operations attribute."""
        return self.cluster.get("ctrl_seqe_of_oper", 0xFF)

    @property
    def max_cool_setpoint_limit(self) -> int:
        """Maximum cooling setpoint."""
        sp_limit = self.cluster.get("max_cool_setpoint_limit")
        if sp_limit is None:
            return self.abs_max_cool_setpoint_limit
        return sp_limit

    @property
    def min_cool_setpoint_limit(self) -> int:
        """Minimum cooling setpoint."""
        sp_limit = self.cluster.get("min_cool_setpoint_limit")
        if sp_limit is None:
            return self.abs_min_cool_setpoint_limit
        return sp_limit

    @property
    def max_heat_setpoint_limit(self) -> int:
        """Maximum heating setpoint."""
        sp_limit = self.cluster.get("max_heat_setpoint_limit")
        if sp_limit is None:
            return self.abs_max_heat_setpoint_limit
        return sp_limit

    @property
    def min_heat_setpoint_limit(self) -> int:
        """Minimum heating setpoint."""
        sp_limit = self.cluster.get("min_heat_setpoint_limit")
        if sp_limit is None:
            return self.abs_min_heat_setpoint_limit
        return sp_limit

    @property
    def local_temp(self) -> int | None:
        """Thermostat temperature."""
        return self.cluster.get("local_temp")

    @property
    def occupancy(self) -> int | None:
        """Is occupancy detected."""
        return self.cluster.get("occupancy")

    @property
    def occupied_cooling_setpoint(self) -> int | None:
        """Temperature when room is occupied."""
        return self.cluster.get("occupied_cooling_setpoint")

    @property
    def occupied_heating_setpoint(self) -> int | None:
        """Temperature when room is occupied."""
        return self.cluster.get("occupied_heating_setpoint")

    @property
    def pi_cooling_demand(self) -> int:
        """Cooling demand."""
        return self.cluster.get("pi_cooling_demand")

    @property
    def pi_heating_demand(self) -> int:
        """Heating demand."""
        return self.cluster.get("pi_heating_demand")

    @property
    def running_mode(self) -> int | None:
        """Thermostat running mode."""
        return self.cluster.get("running_mode")

    @property
    def running_state(self) -> int | None:
        """Thermostat running state, state of heat, cool, fan relays."""
        return self.cluster.get("running_state")

    @property
    def system_mode(self) -> int | None:
        """System mode."""
        return self.cluster.get("system_mode")

    @property
    def unoccupied_cooling_setpoint(self) -> int | None:
        """Temperature when room is not occupied."""
        return self.cluster.get("unoccupied_cooling_setpoint")

    @property
    def unoccupied_heating_setpoint(self) -> int | None:
        """Temperature when room is not occupied."""
        return self.cluster.get("unoccupied_heating_setpoint")

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute update cluster."""
        attr_name = self.cluster.attributes.get(attrid, [attrid])[0]
        self.debug(
            "Attribute report '%s'[%s] = %s", self.cluster.name, attr_name, value
        )
        self.emit(
            CLUSTER_HANDLER_EVENT,
            ClusterAttributeUpdatedEvent(
                id=attrid,
                name=attr_name,
                value=value,
            ),
        )

    async def async_set_operation_mode(self, mode: Any) -> bool:
        """Set Operation mode."""
        if not await self.write_attributes({"system_mode": mode}):
            self.debug("couldn't set '%s' operation mode", mode)
            return False

        self.debug("set system to %s", mode)
        return True

    async def async_set_heating_setpoint(
        self, temperature: int, is_away: bool = False
    ) -> bool:
        """Set heating setpoint."""
        if is_away:
            data = {"unoccupied_heating_setpoint": temperature}
        else:
            data = {"occupied_heating_setpoint": temperature}
        if not await self.write_attributes(data):
            self.debug("couldn't set heating setpoint")
            return False

        return True

    async def async_set_cooling_setpoint(
        self, temperature: int, is_away: bool = False
    ) -> bool:
        """Set cooling setpoint."""
        if is_away:
            data = {"unoccupied_cooling_setpoint": temperature}
        else:
            data = {"occupied_cooling_setpoint": temperature}
        if not await self.write_attributes(data):
            self.debug("couldn't set cooling setpoint")
            return False
        self.debug("set cooling setpoint to %s", temperature)
        return True

    async def get_occupancy(self) -> bool | None:
        """Get unreportable occupancy attribute."""
        try:
            res, fail = await self.cluster.read_attributes(["occupancy"])
            self.debug("read 'occupancy' attr, success: %s, fail: %s", res, fail)
            if "occupancy" not in res:
                return None
            return bool(self.occupancy)
        except ZigbeeException as ex:
            self.debug("Couldn't read 'occupancy' attribute: %s", ex)
            return None

    async def write_attributes(self, data: dict, **kwargs: Any) -> bool:
        """Write attributes helper."""
        try:
            res = await self.cluster.write_attributes(data, **kwargs)
        except ZigbeeException as exc:
            self.debug("couldn't write %s: %s", data, exc)
            return False

        self.debug("wrote %s attrs, Status: %s", data, res)
        return self.check_result(res)

    @staticmethod
    def check_result(res: Any) -> bool:
        """Normalize the result."""
        if not isinstance(res, list):
            return False

        return all(record.status == Status.SUCCESS for record in res[0])


@registries.CLUSTER_HANDLER_REGISTRY.register(hvac.UserInterface.cluster_id)
class UserInterface(ClusterHandler):
    """User interface (thermostat) cluster handler."""
