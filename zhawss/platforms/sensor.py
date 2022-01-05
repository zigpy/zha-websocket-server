"""Sensor platform for zhawss."""

import functools
from typing import List, Union

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import (
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
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.registries import SMARTTHINGS_HUMIDITY_CLUSTER
from zhawss.zigbee.types import DeviceType, EndpointType

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SENSOR)
CLUSTER_HANDLER_ST_HUMIDITY_CLUSTER = f"channel_0x{SMARTTHINGS_HUMIDITY_CLUSTER:04x}"


class Sensor(PlatformEntity):
    """Representation of a zhawss sensor."""

    PLATFORM = Platform.SENSOR
    SENSOR_ATTR: Union[int, str, None] = None
    _decimals: int = 1
    _divisor: int = 1
    _multiplier: int = 1
    _unit: Union[str, None] = None

    @classmethod
    def create_platform_entity(
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return a platform entity if it is a supported configuration, otherwise return None
        """
        cluster_handler = cluster_handlers[0]
        if cls.SENSOR_ATTR in cluster_handler.cluster.unsupported_attributes:
            return None

        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

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
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.BATTERY
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _unit = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    """

    @classmethod
    def create_platform_entity(
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Unlike any other entity, PowerConfiguration cluster may not support
        battery_percent_remaining attribute, but zha-device-handlers takes care of it
        so create the entity regardless
        """

        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurement(Sensor):
    """Active power measurement."""

    SENSOR_ATTR = "active_power"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.POWER
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _unit = POWER_WATT
    _div_mul_prefix = "ac_power"
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementApparentPower(
    ElectricalMeasurement, id_suffix="apparent_power"
):
    """Apparent power measurement."""

    SENSOR_ATTR = "apparent_power"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.APPARENT_POWER
    _unit = POWER_VOLT_AMPERE
    _div_mul_prefix = "ac_power"
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementRMSCurrent(ElectricalMeasurement, id_suffix="rms_current"):
    """RMS current measurement."""

    SENSOR_ATTR = "rms_current"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.CURRENT
    _unit = ELECTRIC_CURRENT_AMPERE
    _div_mul_prefix = "ac_current"
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT)
class ElectricalMeasurementRMSVoltage(ElectricalMeasurement, id_suffix="rms_voltage"):
    """RMS Voltage measurement."""

    SENSOR_ATTR = "rms_voltage"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.CURRENT
    _unit = ELECTRIC_POTENTIAL_VOLT
    _div_mul_prefix = "ac_voltage"
    """


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
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.HUMIDITY
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _divisor = 100
    _unit = PERCENTAGE
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SOIL_MOISTURE)
class SoilMoisture(Sensor):
    """Soil Moisture sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.HUMIDITY
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _divisor = 100
    _unit = PERCENTAGE
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_LEAF_WETNESS)
class LeafWetness(Sensor):
    """Leaf Wetness sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.HUMIDITY
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _divisor = 100
    _unit = PERCENTAGE
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_ILLUMINANCE)
class Illuminance(Sensor):
    """Illuminance Sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.ILLUMINANCE
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _unit = LIGHT_LUX
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SMARTENERGY_METERING)
class SmartEnergyMetering(Sensor):
    """Metering sensor."""

    SENSOR_ATTR: Union[int, str] = "instantaneous_demand"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.POWER
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_SMARTENERGY_METERING)
class SmartEnergySummation(SmartEnergyMetering, id_suffix="summation_delivered"):
    """Smart Energy Metering summation sensor."""

    SENSOR_ATTR: Union[int, str] = "current_summ_delivered"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.ENERGY
    _attr_state_class: SensorStateClass = SensorStateClass.TOTAL_INCREASING
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_PRESSURE)
class Pressure(Sensor):
    """Pressure sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.PRESSURE
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _unit = PRESSURE_HPA
    """


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_TEMPERATURE)
class Temperature(Sensor):
    """Temperature Sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.TEMPERATURE
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _divisor = 100
    _unit = TEMP_CELSIUS
    """


@MULTI_MATCH(cluster_handler_names="carbon_dioxide_concentration")
class CarbonDioxideConcentration(Sensor):
    """Carbon Dioxide Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.CO2
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _multiplier = 1e6
    _unit = CONCENTRATION_PARTS_PER_MILLION
    """


@MULTI_MATCH(cluster_handler_names="carbon_monoxide_concentration")
class CarbonMonoxideConcentration(Sensor):
    """Carbon Monoxide Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.CO
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _multiplier = 1e6
    _unit = CONCENTRATION_PARTS_PER_MILLION
    """


@MULTI_MATCH(generic_ids="channel_0x042e", stop_on_match_group="voc_level")
@MULTI_MATCH(cluster_handler_names="voc_level", stop_on_match_group="voc_level")
class VOCLevel(Sensor):
    """VOC Level sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _multiplier = 1e6
    _unit = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    """


@MULTI_MATCH(
    cluster_handler_names="voc_level",
    models="lumi.airmonitor.acn01",
    stop_on_match_group="voc_level",
)
class PPBVOCLevel(Sensor):
    """VOC Level sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _multiplier = 1
    _unit = CONCENTRATION_PARTS_PER_BILLION
    """


@MULTI_MATCH(cluster_handler_names="formaldehyde_concentration")
class FormaldehydeConcentration(Sensor):
    """Formaldehyde Concentration sensor."""

    SENSOR_ATTR = "measured_value"
    """TODO
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _decimals = 0
    _multiplier = 1e6
    _unit = CONCENTRATION_PARTS_PER_MILLION
    """


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class ThermostatHVACAction(Sensor, id_suffix="hvac_action"):
    """Thermostat HVAC action sensor."""

    @classmethod
    def create_platform_entity(
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return entity if it is a supported configuration, otherwise return None
        """

        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_THERMOSTAT},
    manufacturers="Sinope Technologies",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class SinopeHVACAction(ThermostatHVACAction):
    """Sinope Thermostat HVAC action sensor."""


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BASIC)
class RSSISensor(Sensor, id_suffix="rssi"):
    """RSSI sensor for a device."""

    """TODO
    _state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _device_class: SensorDeviceClass = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    """

    @classmethod
    def create_platform_entity(
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return entity if it is a supported configuration, otherwise return None
        """
        key = f"{CLUSTER_HANDLER_BASIC}_{cls.unique_id_suffix}"
        if PLATFORM_ENTITIES.prevent_entity_creation(Platform.SENSOR, device.ieee, key):
            return None
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_BASIC)
class LQISensor(RSSISensor, id_suffix="lqi"):
    """LQI sensor for a device."""
