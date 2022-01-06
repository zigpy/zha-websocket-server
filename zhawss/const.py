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

MESSAGE_TYPE = "message_type"


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
