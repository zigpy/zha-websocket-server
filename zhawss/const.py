"""Constants."""


from typing import Final

import voluptuous

COMMAND = "command"
COMMAND_GET_DEVICES = "get_devices"
COMMAND_PERMIT_JOINING = "permit_joining"
COMMAND_START_NETWORK = "start_network"
COMMAND_STOP_NETWORK = "stop_network"
COMMAND_STOP_SERVER = "stop_server"

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
MESSAGE_TYPE_EVENT = "event"
MESSAGE_TYPE_RESULT = "result"

DEVICES = "devices"
DURATION = "duration"
ERROR_CODE = "error_code"
MESSAGE_ID = "message_id"
SUCCESS = "success"
WEBSOCKET_API = "websocket_api"
ZIGBEE_ERROR_CODE = "zigbee_error_code"

MINIMAL_MESSAGE_SCHEMA: Final = voluptuous.Schema(
    {voluptuous.Required(COMMAND): str},
    extra=voluptuous.ALLOW_EXTRA,
)
