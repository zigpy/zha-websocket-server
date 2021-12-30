"""Websocket API for zhawss."""

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH

from zhawss.const import (
    COMMAND,
    COMMAND_START_NETWORK,
    COMMAND_STOP_NETWORK,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
)

from . import async_register_command, decorators


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_START_NETWORK,
        vol.Required(CONF_RADIO_TYPE): str,
        vol.Required(CONF_DEVICE): vol.Schema(
            {
                vol.Required(CONF_DEVICE_PATH): str,
                vol.Required(CONF_FLOWCONTROL): str,
                vol.Required(CONF_BAUDRATE): decorators.POSITIVE_INT,
            }
        ),
        vol.Required(CONF_DATABASE): str,
        vol.Required(CONF_ENABLE_QUIRKS): bool,
    }
)
async def start_network(controller, websocket, message):
    """Start the Zigbee network."""
    await controller.start_network(message)


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_STOP_NETWORK,
    }
)
async def stop_network(controller, websocket, message):
    """Stop the Zigbee network."""
    await controller.stop_network(message)


def load_api(controller):
    """Load the api command handlers."""
    async_register_command(controller, start_network)
    async_register_command(controller, stop_network)
