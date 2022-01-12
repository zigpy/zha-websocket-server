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

    # Light API commands
    LIGHT_TURN_ON = "light_turn_on"
    LIGHT_TURN_OFF = "light_turn_off"


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


COMMAND: Final[str] = "command"
CONF_BAUDRATE: Final[str] = "baudrate"
CONF_CUSTOM_QUIRKS_PATH: Final[str] = "custom_quirks_path"
CONF_DATABASE: Final[str] = "database_path"
CONF_DEFAULT_LIGHT_TRANSITION: Final[str] = "default_light_transition"
CONF_DEVICE_CONFIG: Final[str] = "device_config"
CONF_ENABLE_IDENTIFY_ON_JOIN: Final[str] = "enable_identify_on_join"
CONF_ENABLE_QUIRKS: Final[str] = "enable_quirks"
CONF_FLOWCONTROL: Final[str] = "flow_control"
CONF_RADIO_TYPE: Final[str] = "radio_type"
CONF_USB_PATH: Final[str] = "usb_path"
CONF_ZIGPY: Final[str] = "zigpy_config"

DEVICE: Final[str] = "device"

EVENT: Final[str] = "event"
EVENT_TYPE: Final[str] = "event_type"

MESSAGE_TYPE: Final[str] = "message_type"

IEEE: Final[str] = "ieee"
NWK: Final[str] = "nwk"
PAIRING_STATUS: Final[str] = "pairing_status"


DEVICES: Final[str] = "devices"
DURATION: Final[str] = "duration"
ERROR_CODE: Final[str] = "error_code"
MESSAGE_ID: Final[str] = "message_id"
SUCCESS: Final[str] = "success"
WEBSOCKET_API: Final[str] = "websocket_api"
ZIGBEE_ERROR_CODE: Final[str] = "zigbee_error_code"


MINIMAL_MESSAGE_SCHEMA: Final = voluptuous.Schema(
    {
        voluptuous.Required(COMMAND): voluptuous.In(
            [str(item) for item in APICommands]
        ),
        voluptuous.Required(MESSAGE_ID): int,
    },
    extra=voluptuous.ALLOW_EXTRA,
)
