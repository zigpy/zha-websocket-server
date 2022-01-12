"""Websocket API for zhawss."""

import logging
from typing import Any, Awaitable

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.device import Device
from zigpy.types.named import EUI64

from zhawss.const import (
    COMMAND,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
    DEVICES,
    DURATION,
    IEEE,
    MESSAGE_ID,
    APICommands,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType

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
) -> Awaitable[None]:
    """Start the Zigbee network."""
    await server.controller.start_network(message)
    client.send_result_success(
        message[MESSAGE_ID], {COMMAND: APICommands.START_NETWORK}
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.STOP_NETWORK),
    }
)
async def stop_network(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Stop the Zigbee network."""
    await server.controller.stop_network()
    client.send_result_success(message[MESSAGE_ID], {COMMAND: APICommands.STOP_NETWORK})


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.GET_DEVICES),
    }
)
async def get_devices(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Get Zigbee devices."""
    devices: list[Device] = server.controller.get_devices()
    _LOGGER.info("devices: %s", devices)
    client.send_result_success(
        message[MESSAGE_ID], {COMMAND: APICommands.GET_DEVICES, DEVICES: devices}
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.PERMIT_JOINING),
        vol.Optional(DURATION, default=60): vol.All(vol.Coerce(int), vol.Range(0, 254)),
    }
)
async def permit_joining(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.permit(message[DURATION])
    client.send_result_success(
        message[MESSAGE_ID],
        {COMMAND: APICommands.PERMIT_JOINING, DURATION: message[DURATION]},
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.REMOVE_DEVICE),
        vol.Required(IEEE): str,
    }
)
async def remove_device(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.remove(
        EUI64.convert(message["ieee"])
    )
    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: APICommands.REMOVE_DEVICE,
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, start_network)
    register_api_command(server, stop_network)
    register_api_command(server, get_devices)
    register_api_command(server, permit_joining)
    register_api_command(server, remove_device)
