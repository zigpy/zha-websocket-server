"""Constants for the cluster module."""

REPORT_CONFIG_ATTR_PER_REQ = 3
REPORT_CONFIG_MAX_INT = 900
REPORT_CONFIG_MAX_INT_BATTERY_SAVE = 10800
REPORT_CONFIG_MIN_INT = 30
REPORT_CONFIG_MIN_INT_ASAP = 1
REPORT_CONFIG_MIN_INT_IMMEDIATE = 0
REPORT_CONFIG_MIN_INT_OP = 5
REPORT_CONFIG_MIN_INT_BATTERY_SAVE = 3600
REPORT_CONFIG_RPT_CHANGE = 1
REPORT_CONFIG_DEFAULT = (
    REPORT_CONFIG_MIN_INT,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_ASAP = (
    REPORT_CONFIG_MIN_INT_ASAP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_BATTERY_SAVE = (
    REPORT_CONFIG_MIN_INT_BATTERY_SAVE,
    REPORT_CONFIG_MAX_INT_BATTERY_SAVE,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_IMMEDIATE = (
    REPORT_CONFIG_MIN_INT_IMMEDIATE,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
REPORT_CONFIG_OP = (
    REPORT_CONFIG_MIN_INT_OP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_RPT_CHANGE,
)
CLUSTER_READS_PER_REQ = 5

CLUSTER_HANDLER_ACCELEROMETER = "accelerometer"
CLUSTER_HANDLER_BINARY_INPUT = "binary_input"
CLUSTER_HANDLER_ANALOG_INPUT = "analog_input"
CLUSTER_HANDLER_ANALOG_OUTPUT = "analog_output"
CLUSTER_HANDLER_ATTRIBUTE = "attribute"
CLUSTER_HANDLER_BASIC = "basic"
CLUSTER_HANDLER_COLOR = "light_color"
CLUSTER_HANDLER_COVER = "window_covering"
CLUSTER_HANDLER_DOORLOCK = "door_lock"
CLUSTER_HANDLER_ELECTRICAL_MEASUREMENT = "electrical_measurement"
CLUSTER_HANDLER_EVENT_RELAY = "event_relay"
CLUSTER_HANDLER_FAN = "fan"
CLUSTER_HANDLER_HUMIDITY = "humidity"
CLUSTER_HANDLER_SOIL_MOISTURE = "soil_moisture"
CLUSTER_HANDLER_LEAF_WETNESS = "leaf_wetness"
CLUSTER_HANDLER_IAS_ACE = "ias_ace"
CLUSTER_HANDLER_IAS_WD = "ias_wd"
CLUSTER_HANDLER_IDENTIFY = "identify"
CLUSTER_HANDLER_ILLUMINANCE = "illuminance"
CLUSTER_HANDLER_LEVEL = "level"
CLUSTER_HANDLER_MULTISTATE_INPUT = "multistate_input"
CLUSTER_HANDLER_OCCUPANCY = "occupancy"
CLUSTER_HANDLER_ON_OFF = "on_off"
CLUSTER_HANDLER_POWER_CONFIGURATION = "power"
CLUSTER_HANDLER_PRESSURE = "pressure"
CLUSTER_HANDLER_SHADE = "shade"
CLUSTER_HANDLER_SMARTENERGY_METERING = "smartenergy_metering"
CLUSTER_HANDLER_TEMPERATURE = "temperature"
CLUSTER_HANDLER_THERMOSTAT = "thermostat"
CLUSTER_HANDLER_ZDO = "zdo"
CLUSTER_HANDLER_ZONE = ZONE = "ias_zone"