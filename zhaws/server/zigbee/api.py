"""Websocket API for zhawss."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.types.named import EUI64

from zhaws.server.const import (
    COMMAND,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
    DEVICES,
    DURATION,
    IEEE,
    APICommands,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


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
@decorators.async_response
async def start_network(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Start the Zigbee network."""
    await server.controller.start_network(message)
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.STOP_NETWORK),
    }
)
@decorators.async_response
async def stop_network(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Stop the Zigbee network."""
    await server.controller.stop_network()
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.GET_DEVICES),
    }
)
@decorators.async_response
async def get_devices(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Get Zigbee devices."""
    devices: dict[str, Any] = server.controller.get_devices()
    _LOGGER.info("devices: %s", devices)
    client.send_result_success(message, {DEVICES: devices})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.PERMIT_JOINING),
        vol.Optional(DURATION, default=60): vol.All(vol.Coerce(int), vol.Range(0, 254)),
    }
)
@decorators.async_response
async def permit_joining(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.permit(message[DURATION])
    client.send_result_success(
        message,
        {DURATION: message[DURATION]},
    )


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.REMOVE_DEVICE),
        vol.Required(IEEE): str,
    }
)
@decorators.async_response
async def remove_device(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.remove(
        EUI64.convert(message["ieee"])
    )
    client.send_result_success(message)


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, start_network)
    register_api_command(server, stop_network)
    register_api_command(server, get_devices)
    register_api_command(server, permit_joining)
    register_api_command(server, remove_device)
