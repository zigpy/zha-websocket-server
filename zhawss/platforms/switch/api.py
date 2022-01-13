"""WS api for the switch platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum

from zhawss.const import ATTR_UNIQUE_ID, IEEE, MESSAGE_ID
from zhawss.platforms import platform_entity_command_schema, send_result_success
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class SwitchCommands(StrEnum):
    """Switch commands."""

    TURN_ON = "switch_turn_on"
    TURN_OFF = "switch_turn_off"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_ON))
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    try:
        device = server.controller.get_device(message[IEEE])
        switch_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await switch_entity.async_turn_on()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SwitchCommands.TURN_OFF))
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the switch."""
    try:
        device = server.controller.get_device(message[IEEE])
        switch_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await switch_entity.async_turn_off()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
