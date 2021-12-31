"""Websocket API for zhawss."""

import json
import logging
from typing import Any

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.device import Device

from zhawss.const import (
    COMMAND,
    COMMAND_GET_DEVICES,
    COMMAND_PERMIT_JOINING,
    COMMAND_START_NETWORK,
    COMMAND_STOP_NETWORK,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
    DEVICES,
    DURATION,
)
from zhawss.types import ControllerType

from . import async_register_command, decorators

_LOGGER = logging.getLogger(__name__)


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
async def start_network(
    controller: ControllerType, websocket, message: dict[str, Any]
) -> None:
    """Start the Zigbee network."""
    await controller.start_network(message)


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_STOP_NETWORK,
    }
)
async def stop_network(
    controller: ControllerType, websocket, message: dict[str, Any]
) -> None:
    """Stop the Zigbee network."""
    await controller.stop_network(message)


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_GET_DEVICES,
    }
)
async def get_devices(
    controller: ControllerType, websocket, message: dict[str, Any]
) -> None:
    """Get Zigbee devices."""
    devices: list[Device] = controller.get_devices()
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
    message[DEVICES] = output
    await websocket.send(json.dumps(message))


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): COMMAND_PERMIT_JOINING,
        vol.Optional(DURATION, default=60): vol.All(vol.Coerce(int), vol.Range(0, 254)),
    }
)
async def permit_joining(
    controller: ControllerType, websocket, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    await controller.application_controller.permit(message[DURATION])


def load_api(controller) -> None:
    """Load the api command handlers."""
    async_register_command(controller, start_network)
    async_register_command(controller, stop_network)
    async_register_command(controller, get_devices)
    async_register_command(controller, permit_joining)
