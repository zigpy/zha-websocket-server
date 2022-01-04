"""Measurement channels module for Zigbee Home Automation."""
from zigpy.zcl.clusters import measurement

from zhawss.zigbee import registries
from zhawss.zigbee.cluster import ClusterHandler
from zhawss.zigbee.cluster.const import (
    REPORT_CONFIG_DEFAULT,
    REPORT_CONFIG_IMMEDIATE,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
)


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.FlowMeasurement.cluster_id)
class FlowMeasurement(ClusterHandler):
    """Flow Measurement channel."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.IlluminanceLevelSensing.cluster_id
)
class IlluminanceLevelSensing(ClusterHandler):
    """Illuminance Level Sensing channel."""

    REPORT_CONFIG = [{"attr": "level_status", "config": REPORT_CONFIG_DEFAULT}]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.IlluminanceMeasurement.cluster_id
)
class IlluminanceMeasurement(ClusterHandler):
    """Illuminance Measurement channel."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.OccupancySensing.cluster_id)
class OccupancySensing(ClusterHandler):
    """Occupancy Sensing channel."""

    REPORT_CONFIG = [{"attr": "occupancy", "config": REPORT_CONFIG_IMMEDIATE}]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.PressureMeasurement.cluster_id)
class PressureMeasurement(ClusterHandler):
    """Pressure measurement channel."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.RelativeHumidity.cluster_id)
class RelativeHumidity(ClusterHandler):
    """Relative Humidity measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.SoilMoisture.cluster_id)
class SoilMoisture(ClusterHandler):
    """Soil Moisture measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(measurement.LeafWetness.cluster_id)
class LeafWetness(ClusterHandler):
    """Leaf Wetness measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.TemperatureMeasurement.cluster_id
)
class TemperatureMeasurement(ClusterHandler):
    """Temperature measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 50),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.CarbonMonoxideConcentration.cluster_id
)
class CarbonMonoxideConcentration(ClusterHandler):
    """Carbon Monoxide measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.CarbonDioxideConcentration.cluster_id
)
class CarbonDioxideConcentration(ClusterHandler):
    """Carbon Dioxide measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    measurement.FormaldehydeConcentration.cluster_id
)
class FormaldehydeConcentration(ClusterHandler):
    """Formaldehyde measurement channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]
