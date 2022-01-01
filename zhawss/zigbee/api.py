"""Websocket API for zhawss."""

import logging
from typing import Any

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.device import Device

from zhawss.const import (
    COMMAND,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
    DEVICES,
    DURATION,
    MESSAGE_ID,
    APICommands,
)
from zhawss.types import ClientType, ServerType
from zhawss.websocket_api import async_register_command, decorators

_LOGGER = logging.getLogger(__name__)


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.START_NETWORK),
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
async def start_network(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> None:
    """Start the Zigbee network."""
    await server.controller.start_network(message)
    client.send_result_success(message[MESSAGE_ID], {})


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.STOP_NETWORK),
    }
)
async def stop_network(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> None:
    """Stop the Zigbee network."""
    await server.controller.stop_network()
    client.send_result_success(message[MESSAGE_ID], {})


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.GET_DEVICES),
    }
)
async def get_devices(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> None:
    """Get Zigbee devices."""
    devices: list[Device] = server.controller.get_devices()
    _LOGGER.info("devices: %s", devices)
    output = [
        {
            "ieee": str(device.ieee),
            "nwk": device.nwk,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "status": device.status.name,
        }
        for device in devices
    ]
    client.send_result_success(message[MESSAGE_ID], {DEVICES: output})


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.PERMIT_JOINING),
        vol.Optional(DURATION, default=60): vol.All(vol.Coerce(int), vol.Range(0, 254)),
    }
)
async def permit_joining(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.permit(message[DURATION])
    client.send_result_success(message[MESSAGE_ID], {DURATION: message[DURATION]})


def load_api(server) -> None:
    """Load the api command handlers."""
    async_register_command(server, start_network)
    async_register_command(server, stop_network)
    async_register_command(server, get_devices)
    async_register_command(server, permit_joining)
