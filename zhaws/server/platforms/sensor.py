"""Sensor platform for zhawss."""
from __future__ import annotations

import asyncio
import functools
import logging
import numbers
from typing import TYPE_CHECKING, Any, Final, Type, Union

from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_ANALOG_INPUT,
    CLUSTER_HANDLER_BASIC,
    CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT,
    CLUSTER_HANDLER_HUMIDITY,
    CLUSTER_HANDLER_ILLUMINANCE,
    CLUSTER_HANDLER_LEAF_WETNESS,
    CLUSTER_HANDLER_POWER_CONFIGURATION,
    CLUSTER_HANDLER_PRESSURE,
    CLUSTER_HANDLER_SMARTENERGY_METERING,
    CLUSTER_HANDLER_SOIL_MOISTURE,
    CLUSTER_HANDLER_TEMPERATURE,
    CLUSTER_HANDLER_THERMOSTAT,
)
from zhaws.server.zigbee.registries import SMARTTHINGS_HUMIDITY_CLUSTER

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SENSOR)
CLUSTER_HANDLER_ST_HUMIDITY_CLUSTER = f"channel_0x{SMARTTHINGS_HUMIDITY_CLUSTER:04x}"

_LOGGER = logging.getLogger(__name__)

BATTERY_SIZES = {
    0: "No battery",
    1: "Built in",
    2: "Other",
    3: "AA",
    4: "AAA",
    5: "C",
    6: "D",
    7: "CR2",
    8: "CR123A",
    9: "CR2450",
    10: "CR2032",
    11: "CR1632",
    255: "Unknown",
}

CURRENT_HVAC_OFF: Final[str] = "off"
CURRENT_HVAC_HEAT: Final[str] = "heating"
CURRENT_HVAC_COOL: Final[str] = "cooling"
CURRENT_HVAC_DRY: Final[str] = "drying"
CURRENT_HVAC_IDLE: Final[str] = "idle"
CURRENT_HVAC_FAN: Final[str] = "fan"


class Sensor(PlatformEntity):
    """Representation of a zhawss sensor."""

    PLATFORM = Platform.SENSOR
    SENSOR_ATTR: Union[int, str, None] = None
    _REFRESH_INTERVAL = (30, 45)
    _decimals: int = 1
    _divisor: int = 1
    _multiplier: int | float = 1
    _unit: Union[str, None] = None

    @classmethod
    def create_platform_entity(
        cls: Type[Sensor],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return a platform entity if it is a supported configuration, otherwise return None
        """
        cluster_handler = cluster_handlers[0]
        if cls.SENSOR_ATTR in cluster_handler.cluster.unsupported_attributes:
            return None

        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandler = cluster_handlers[0]
        self._cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )
        if self.should_poll:
            self.poller_task = asyncio.create_task(self._refresh())

    def get_state(self) -> dict:
        """Return the state for this sensor."""
        response = super().get_state()
        if self.SENSOR_ATTR is not None:
            raw_state = self._cluster_handler.cluster.get(self.SENSOR_ATTR)
            if raw_state is not None:
                raw_state = self.formatter(raw_state)
            response["state"] = raw_state
        return response

    def formatter(self, value: int) -> Union[int, float]:
        """Numeric pass-through formatter."""
        if self._decimals > 0:
            return round(
                float(value * self._multiplier) / self._divisor, self._decimals
            )
        return round(float(value * self._multiplier) / self._divisor)

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """handle attribute updates from the cluster handler."""
        self.maybe_send_state_changed_event()

    @periodic(_REFRESH_INTERVAL)
    async def _refresh(self) -> None:
        """Refresh the sensor."""
        await self.async_update()

    def to_json(self) -> dict:
        """Return a JSON representation of the sensor."""
        json = super().to_json()
        json["attribute"] = self.SENSOR_ATTR
        json["decimals"] = self._decimals
        json["divisor"] = self._divisor
        json["multiplier"] = self._multiplier
        json["unit"] = self._unit
        return json


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ANALOG_INPUT,
    manufacturers="LUMI",
    models={"lumi.plug", "lumi.plug.maus01", "lumi.plug.mmeu01"},
    stop_on_match_group=CLUSTER_HANDLER_ANALOG_INPUT,
)
@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ANALOG_INPUT,
    manufacturers="Digi",
    stop_on_match_group=CLUSTER_HANDLER_ANALOG_INPUT,
)
class AnalogInput(Sensor):
    """Sensor that displays analog input values."""

    SENSOR_ATTR = "present_value"


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_POWER_CONFIGURATION)
class Battery(Sensor):
    """Battery sensor of power configuration cluster."""

    SENSOR_ATTR = "battery_percentage_remaining"

    @classmethod
    def create_platform_entity(
        cls: Type[Battery],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Unlike any other entity, PowerConfiguration cluster may not support
        battery_percent_remaining attribute, but zha-device-handlers takes care of it
        so create the entity regardless
        """
        if device.is_mains_powered:
            return None
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    @staticmethod
    def formatter(value: int) -> int:
        """Return the state of the entity."""
        # per zcl specs battery percent is reported at 200% ¯\_(ツ)_/¯
        if not isinstance(value, numbers.Number) or value == -1:
            return value
        value = round(value / 2)
        return value

    def get_state(self) -> dict[str, Any]:
        """Return the state for battery sensors."""
        response = super().get_state()
        battery_size = self._cluster_handler.cluster.get("battery_size")
        if battery_size is not None:
            response["battery_size"] = BATTERY_SIZES.get(battery_size, "Unknown")
        battery_quantity = self._cluster_handler.cluster.get("battery_quantity")
        if battery_quantity is not None:
            response["battery_quantity"] = battery_quantity
        battery_voltage = self._cluster_handler.cluster.get("battery_voltage")
        if battery_voltage is not None:
            response["battery_voltage"] = round(battery_voltage / 10, 2)
        return response


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurement(Sensor):
    """Active power measurement."""

    SENSOR_ATTR = "active_power"
    _div_mul_prefix = "ac_power"

    @property
    def should_poll(self) -> bool:
        """Return True if we need to poll for state changes."""
        return True

    def get_state(self) -> dict[str, Any]:
        """Return the state for this sensor."""
        response = super().get_state()
        if self._cluster_handler.measurement_type is not None:
            response["measurement_type"] = self._cluster_handler.measurement_type

        max_attr_name = f"{self.SENSOR_ATTR}_max"
        if (max_v := self._cluster_handler.cluster.get(max_attr_name)) is not None:
            response[max_attr_name] = str(self.formatter(max_v))

        return response

    def formatter(self, value: int) -> Union[int, float]:
        """Return 'normalized' value."""
        multiplier = getattr(
            self._cluster_handler, f"{self._div_mul_prefix}_multiplier"
        )
        divisor = getattr(self._cluster_handler, f"{self._div_mul_prefix}_divisor")
        value = float(value * multiplier) / divisor
        if value < 100 and divisor > 1:
            return round(value, self._decimals)
        return round(value)

    async def async_update(self) -> None:
        """Retrieve latest state."""
        if not self.available:
            return
        await super().async_update()


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementApparentPower(
    ElectricalMeasurement, id_suffix="apparent_power"
):
    """Apparent power measurement."""

    SENSOR_ATTR = "apparent_power"
    _div_mul_prefix = "ac_power"

    @property
    def should_poll(self) -> bool:
        """Poll indirectly by ElectricalMeasurementSensor."""
        return False


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementRMSCurrent(ElectricalMeasurement, id_suffix="rms_current"):
    """RMS current measurement."""

    SENSOR_ATTR = "rms_current"
    _div_mul_prefix = "ac_current"

    @property
    def should_poll(self) -> bool:
        """Poll indirectly by ElectricalMeasurementSensor."""
        return False


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementRMSVoltage(ElectricalMeasurement, id_suffix="rms_voltage"):
    """RMS Voltage measurement."""

    SENSOR_ATTR = "rms_voltage"
    _div_mul_prefix = "ac_voltage"

    @property
    def should_poll(self) -> bool:
        """Poll indirectly by ElectricalMeasurementSensor."""
        return False


@MULTI_MATCH(
    generic_ids=CLUSTER_HANDLER_ST_HUMIDITY_CLUSTER,
    stop_on_match_group=CLUSTER_HANDLER_HUMIDITY,
)
@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_HUMIDITY,
    stop_on_match_group=CLUSTER_HANDLER_HUMIDITY,
)
class Humidity(Sensor):
    """Humidity sensor."""

    SENSOR_ATTR = "measured_value"
    _divisor = 100


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SOIL_MOISTURE)
class SoilMoisture(Sensor):
    """Soil Moisture sensor."""

    SENSOR_ATTR = "measured_value"
    _divisor = 100


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_LEAF_WETNESS)
class LeafWetness(Sensor):
    """Leaf Wetness sensor."""

    SENSOR_ATTR = "measured_value"
    _divisor = 100


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ILLUMINANCE)
class Illuminance(Sensor):
    """Illuminance Sensor."""

    SENSOR_ATTR = "measured_value"

    @staticmethod
    def formatter(value: int) -> float:
        """Convert illumination data."""
        return round(pow(10, ((value - 1) / 10000)), 1)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SMARTENERGY_METERING)
class SmartEnergyMetering(Sensor):
    """Metering sensor."""

    SENSOR_ATTR: Union[int, str] = "instantaneous_demand"

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._unit = self._cluster_handler.unit_of_measurement

    def formatter(self, value: int) -> Union[int, float]:
        """Pass through cluster handler formatter."""
        return self._cluster_handler.demand_formatter(value)

    def get_state(self) -> dict[str, Any]:
        """Return state for this sensor."""
        response = super().get_state()
        if self._cluster_handler.device_type is not None:
            response["device_type"] = self._cluster_handler.device_type
        if (status := self._cluster_handler.metering_status) is not None:
            response["status"] = str(status)[len(status.__class__.__name__) + 1 :]
        return response


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SMARTENERGY_METERING)
class SmartEnergySummation(SmartEnergyMetering, id_suffix="summation_delivered"):
    """Smart Energy Metering summation sensor."""

    SENSOR_ATTR: Union[int, str] = "current_summ_delivered"

    def formatter(self, value: int) -> Union[int, float]:
        """Numeric pass-through formatter."""
        if self._cluster_handler.unit_of_measurement != 0:
            return self._cluster_handler.summa_formatter(value)

        cooked = (
            float(self._cluster_handler.multiplier * value)
            / self._cluster_handler.divisor
        )
        return round(cooked, 3)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_PRESSURE)
class Pressure(Sensor):
    """Pressure sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_TEMPERATURE)
class Temperature(Sensor):
    """Temperature Sensor."""

    SENSOR_ATTR = "measured_value"
    _divisor = 100


@MULTI_MATCH(cluster_handler_names="carbon_dioxide_concentration")
class CarbonDioxideConcentration(Sensor):
    """Carbon Dioxide Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0
    _multiplier = 1e6


@MULTI_MATCH(cluster_handler_names="carbon_monoxide_concentration")
class CarbonMonoxideConcentration(Sensor):
    """Carbon Monoxide Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0
    _multiplier = 1e6


@MULTI_MATCH(generic_ids="channel_0x042e", stop_on_match_group="voc_level")
@MULTI_MATCH(cluster_handler_names="voc_level", stop_on_match_group="voc_level")
class VOCLevel(Sensor):
    """VOC Level sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0
    _multiplier = 1e6


@MULTI_MATCH(
    cluster_handler_names="voc_level",
    models="lumi.airmonitor.acn01",
    stop_on_match_group="voc_level",
)
class PPBVOCLevel(Sensor):
    """VOC Level sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0
    _multiplier = 1


@MULTI_MATCH(cluster_handler_names="formaldehyde_concentration")
class FormaldehydeConcentration(Sensor):
    """Formaldehyde Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    _decimals = 0
    _multiplier = 1e6


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class ThermostatHVACAction(Sensor, id_suffix="hvac_action"):
    """Thermostat HVAC action sensor."""

    @classmethod
    def create_platform_entity(
        cls: Type[ThermostatHVACAction],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return entity if it is a supported configuration, otherwise return None
        """

        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    @property
    def _rm_rs_action(self) -> Union[str, None]:
        """Return the current HVAC action based on running mode and running state."""

        if (running_state := self._cluster_handler.running_state) is None:
            return None

        rs_heat = (
            self._cluster_handler.RunningState.Heat_State_On
            | self._cluster_handler.RunningState.Heat_2nd_Stage_On
        )
        if running_state & rs_heat:
            return CURRENT_HVAC_HEAT

        rs_cool = (
            self._cluster_handler.RunningState.Cool_State_On
            | self._cluster_handler.RunningState.Cool_2nd_Stage_On
        )
        if running_state & rs_cool:
            return CURRENT_HVAC_COOL

        running_state = self._cluster_handler.running_state
        if running_state and running_state & (
            self._cluster_handler.RunningState.Fan_State_On
            | self._cluster_handler.RunningState.Fan_2nd_Stage_On
            | self._cluster_handler.RunningState.Fan_3rd_Stage_On
        ):
            return CURRENT_HVAC_FAN

        running_state = self._cluster_handler.running_state
        if running_state and running_state & self._cluster_handler.RunningState.Idle:
            return CURRENT_HVAC_IDLE

        if self._cluster_handler.system_mode != self._cluster_handler.SystemMode.Off:
            return CURRENT_HVAC_IDLE
        return CURRENT_HVAC_OFF

    @property
    def _pi_demand_action(self) -> Union[str, None]:
        """Return the current HVAC action based on pi_demands."""

        heating_demand = self._cluster_handler.pi_heating_demand
        if heating_demand is not None and heating_demand > 0:
            return CURRENT_HVAC_HEAT
        cooling_demand = self._cluster_handler.pi_cooling_demand
        if cooling_demand is not None and cooling_demand > 0:
            return CURRENT_HVAC_COOL

        if self._cluster_handler.system_mode != self._cluster_handler.SystemMode.Off:
            return CURRENT_HVAC_IDLE
        return CURRENT_HVAC_OFF

    def get_state(self) -> dict:
        """Return the current HVAC action."""
        response = super().get_state()
        if (
            self._cluster_handler.pi_heating_demand is None
            and self._cluster_handler.pi_cooling_demand is None
        ):
            response["state"] = self._rm_rs_action
        response["state"] = self._pi_demand_action
        return response


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_THERMOSTAT},
    manufacturers="Sinope Technologies",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class SinopeHVACAction(ThermostatHVACAction):
    """Sinope Thermostat HVAC action sensor."""

    @property
    def _rm_rs_action(self) -> Union[str, None]:
        """Return the current HVAC action based on running mode and running state."""

        running_mode = self._cluster_handler.running_mode
        if running_mode == self._cluster_handler.RunningMode.Heat:
            return CURRENT_HVAC_HEAT
        if running_mode == self._cluster_handler.RunningMode.Cool:
            return CURRENT_HVAC_COOL

        running_state = self._cluster_handler.running_state
        if running_state and running_state & (
            self._cluster_handler.RunningState.Fan_State_On
            | self._cluster_handler.RunningState.Fan_2nd_Stage_On
            | self._cluster_handler.RunningState.Fan_3rd_Stage_On
        ):
            return CURRENT_HVAC_FAN
        if (
            self._cluster_handler.system_mode != self._cluster_handler.SystemMode.Off
            and running_mode == self._cluster_handler.SystemMode.Off
        ):
            return CURRENT_HVAC_IDLE
        return CURRENT_HVAC_OFF


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BASIC)
class RSSISensor(Sensor, id_suffix="rssi"):
    """RSSI sensor for a device."""

    @classmethod
    def create_platform_entity(
        cls: Type[RSSISensor],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return entity if it is a supported configuration, otherwise return None
        """
        key = f"{CLUSTER_HANDLER_BASIC}_{cls.unique_id_suffix}"
        if PLATFORM_ENTITIES.prevent_entity_creation(Platform.SENSOR, device.ieee, key):
            return None
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    def get_state(self) -> dict:
        """Return the state of the sensor."""
        response = super().get_state()
        response["state"] = getattr(self.device.device, self.unique_id_suffix)  # type: ignore #TODO fix type hint
        return response

    @property
    def should_poll(self) -> bool:
        """Poll the sensor for current state."""
        return True


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BASIC)
class LQISensor(RSSISensor, id_suffix="lqi"):
    """LQI sensor for a device."""


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BASIC)
class LastSeenSensor(RSSISensor, id_suffix="last_seen"):
    """Last seen sensor for a device."""
