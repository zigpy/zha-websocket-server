"""Measurement cluster handlers module for zhawss."""
from zigpy.zcl.clusters import measurement

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import ClusterHandler
from zhaws.server.zigbee.cluster.const import (
    REPORT_CONFIG_DEFAULT,
    REPORT_CONFIG_IMMEDIATE,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
)


@registries.CLUSTER_HANDLER_REGISTRY.register(measurement.FlowMeasurement.cluster_id)
class FlowMeasurement(ClusterHandler):
    """Flow Measurement cluster handler."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.IlluminanceLevelSensing.cluster_id
)
class IlluminanceLevelSensing(ClusterHandler):
    """Illuminance Level Sensing cluster handler."""

    REPORT_CONFIG = [{"attr": "level_status", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.IlluminanceMeasurement.cluster_id
)
class IlluminanceMeasurement(ClusterHandler):
    """Illuminance Measurement cluster handler."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(measurement.OccupancySensing.cluster_id)
class OccupancySensing(ClusterHandler):
    """Occupancy Sensing cluster handler."""

    REPORT_CONFIG = [{"attr": "occupancy", "config": REPORT_CONFIG_IMMEDIATE}]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.PressureMeasurement.cluster_id
)
class PressureMeasurement(ClusterHandler):
    """Pressure measurement cluster handler."""

    REPORT_CONFIG = [{"attr": "measured_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(measurement.RelativeHumidity.cluster_id)
class RelativeHumidity(ClusterHandler):
    """Relative Humidity measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(measurement.SoilMoisture.cluster_id)
class SoilMoisture(ClusterHandler):
    """Soil Moisture measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(measurement.LeafWetness.cluster_id)
class LeafWetness(ClusterHandler):
    """Leaf Wetness measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 100),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.TemperatureMeasurement.cluster_id
)
class TemperatureMeasurement(ClusterHandler):
    """Temperature measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 50),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.CarbonMonoxideConcentration.cluster_id
)
class CarbonMonoxideConcentration(ClusterHandler):
    """Carbon Monoxide measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.CarbonDioxideConcentration.cluster_id
)
class CarbonDioxideConcentration(ClusterHandler):
    """Carbon Dioxide measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]


@registries.CLUSTER_HANDLER_REGISTRY.register(
    measurement.FormaldehydeConcentration.cluster_id
)
class FormaldehydeConcentration(ClusterHandler):
    """Formaldehyde measurement cluster handler."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 0.000001),
        }
    ]
