"""Constants for the cluster module."""

from typing import Final, Tuple

REPORT_CONFIG_ATTR_PER_REQ: Final[int] = 3
REPORT_CONFIG_MAX_INT: Final[int] = 900
REPORT_CONFIG_MAX_INT_BATTERY_SAVE: Final[int] = 10800
REPORT_CONFIG_MIN_INT: Final[int] = 30
REPORT_CONFIG_MIN_INT_ASAP: Final[int] = 1
REPORT_CONFIG_MIN_INT_IMMEDIATE: Final[int] = 0
REPORT_CONFIG_MIN_INT_OP: Final[int] = 5
REPORT_CONFIG_MIN_INT_BATTERY_SAVE: Final[int] = 3600
REPORT_CONFIG_RPT_CHANGE: Final[int] = 1
REPORT_CONFIG_DEFAULT: Tuple[int, int, int] = (
    REPORT_CONFIG_MIN_INT,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_ASAP: Tuple[int, int, int] = (
    REPORT_CONFIG_MIN_INT_ASAP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_BATTERY_SAVE: Tuple[int, int, int] = (
    REPORT_CONFIG_MIN_INT_BATTERY_SAVE,
    REPORT_CONFIG_MAX_INT_BATTERY_SAVE,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_IMMEDIATE: Tuple[int, int, int] = (
    REPORT_CONFIG_MIN_INT_IMMEDIATE,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_OP: Tuple[int, int, int] = (
    REPORT_CONFIG_MIN_INT_OP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
CLUSTER_READS_PER_REQ: Final[int] = 5

CLUSTER_HANDLER_ACCELEROMETER: Final[str] = "accelerometer"
CLUSTER_HANDLER_BINARY_INPUT: Final[str] = "binary_input"
CLUSTER_HANDLER_ANALOG_INPUT: Final[str] = "analog_input"
CLUSTER_HANDLER_ANALOG_OUTPUT: Final[str] = "analog_output"
CLUSTER_HANDLER_ATTRIBUTE: Final[str] = "attribute"
CLUSTER_HANDLER_BASIC: Final[str] = "basic"
CLUSTER_HANDLER_COLOR: Final[str] = "light_color"
CLUSTER_HANDLER_COVER: Final[str] = "window_covering"
CLUSTER_HANDLER_DOORLOCK: Final[str] = "door_lock"
CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT: Final[str] = "electrical_measurement"
CLUSTER_HANDLER_EVENT_RELAY: Final[str] = "event_relay"
CLUSTER_HANDLER_FAN: Final[str] = "fan"
CLUSTER_HANDLER_HUMIDITY: Final[str] = "humidity"
CLUSTER_HANDLER_SOIL_MOISTURE: Final[str] = "soil_moisture"
CLUSTER_HANDLER_LEAF_WETNESS: Final[str] = "leaf_wetness"
CLUSTER_HANDLER_IAS_ACE: Final[str] = "ias_ace"
CLUSTER_HANDLER_IAS_WD: Final[str] = "ias_wd"
CLUSTER_HANDLER_IDENTIFY: Final[str] = "identify"
CLUSTER_HANDLER_ILLUMINANCE: Final[str] = "illuminance"
CLUSTER_HANDLER_LEVEL: Final[str] = "level"
CLUSTER_HANDLER_MULTISTATE_INPUT: Final[str] = "multistate_input"
CLUSTER_HANDLER_OCCUPANCY: Final[str] = "occupancy"
CLUSTER_HANDLER_ON_OFF: Final[str] = "on_off"
CLUSTER_HANDLER_POWER_CONFIGURATION: Final[str] = "power"
CLUSTER_HANDLER_PRESSURE: Final[str] = "pressure"
CLUSTER_HANDLER_SHADE: Final[str] = "shade"
CLUSTER_HANDLER_SMARTENERGY_METERING: Final[str] = "smartenergy_metering"
CLUSTER_HANDLER_TEMPERATURE: Final[str] = "temperature"
CLUSTER_HANDLER_THERMOSTAT: Final[str] = "thermostat"
CLUSTER_HANDLER_ZDO: Final[str] = "zdo"
ZONE: Final[str] = "ias_zone"
CLUSTER_HANDLER_ZONE: Final[str] = ZONE
