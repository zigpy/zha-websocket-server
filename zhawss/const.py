"""Constants."""

from typing import Final

import voluptuous

try:
    from enum import StrEnum
except ImportError:
    from backports.strenum import StrEnum


class APICommands(StrEnum):
    """WS API commands."""

    # Zigbee API commands
    GET_DEVICES = "get_devices"
    PERMIT_JOINING = "permit_joining"
    REMOVE_DEVICE = "remove_device"
    START_NETWORK = "start_network"
    STOP_NETWORK = "stop_network"

    # Server API commands
    STOP_SERVER = "stop_server"


class MessageTypes(StrEnum):
    """WS message types."""

    EVENT = "event"
    RESULT = "result"


class EventTypes(StrEnum):
    """WS event types."""

    CONTROLLER_EVENT = "controller_event"
    PLATFORM_ENTITY_EVENT = "platform_entity_event"
    RAW_ZCL_EVENT = "raw_zcl_event"


class ControllerEvents(StrEnum):
    """WS controller events."""

    DEVICE_JOINED = "device_joined"
    RAW_DEVICE_INITIALIZED = "raw_device_initialized"
    DEVICE_REMOVED = "device_removed"
    DEVICE_LEFT = "device_left"
    DEVICE_FULLY_INITIALIZED = "device_fully_initialized"
    DEVICE_CONFIGURED = "device_configured"


class PlatformEntityEvents(StrEnum):
    """WS platform entity events."""

    PLATFORM_ENTITY_STATE_CHANGED = "platform_entity_state_changed"


class RawZCLEvents(StrEnum):
    """WS raw ZCL events."""

    ATTRIBUTE_UPDATED = "attribute_updated"


COMMAND = "command"
CONF_BAUDRATE = "baudrate"
CONF_CUSTOM_QUIRKS_PATH = "custom_quirks_path"
CONF_DATABASE = "database_path"
CONF_DEFAULT_LIGHT_TRANSITION = "default_light_transition"
CONF_DEVICE_CONFIG = "device_config"
CONF_ENABLE_IDENTIFY_ON_JOIN = "enable_identify_on_join"
CONF_ENABLE_QUIRKS = "enable_quirks"
CONF_FLOWCONTROL = "flow_control"
CONF_RADIO_TYPE = "radio_type"
CONF_USB_PATH = "usb_path"
CONF_ZIGPY = "zigpy_config"

DEVICE = "device"

EVENT = "event"
EVENT_TYPE = "event_type"

MESSAGE_TYPE = "message_type"

IEEE = "ieee"
NWK = "nwk"
PAIRING_STATUS = "pairing_status"


DEVICES = "devices"
DURATION = "duration"
ERROR_CODE = "error_code"
MESSAGE_ID = "message_id"
SUCCESS = "success"
WEBSOCKET_API = "websocket_api"
ZIGBEE_ERROR_CODE = "zigbee_error_code"


MINIMAL_MESSAGE_SCHEMA: Final = voluptuous.Schema(
    {
        voluptuous.Required(COMMAND): voluptuous.In(
            [str(item) for item in APICommands]
        ),
        voluptuous.Required(MESSAGE_ID): int,
    },
    extra=voluptuous.ALLOW_EXTRA,
)
