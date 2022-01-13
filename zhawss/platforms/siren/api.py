"""WS api for the siren platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import ATTR_UNIQUE_ID, IEEE, MESSAGE_ID
from zhawss.platforms import platform_entity_command_schema, send_result_success
from zhawss.platforms.siren import ATTR_DURATION, ATTR_TONE, ATTR_VOLUME_LEVEL
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class SirenCommands(StrEnum):
    """Siren commands."""

    TURN_ON = "siren_turn_on"
    TURN_OFF = "siren_turn_off"


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        SirenCommands.TURN_ON,
        {
            vol.Optional(ATTR_DURATION): int,
            vol.Optional(ATTR_VOLUME_LEVEL): int,
            vol.Optional(ATTR_TONE): str,
        },
    )
)
async def turn_on(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the siren."""
    try:
        device = server.controller.get_device(message[IEEE])
        siren_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await siren_entity.async_turn_on(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(SirenCommands.TURN_OFF))
async def turn_off(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Turn on the siren."""
    try:
        device = server.controller.get_device(message[IEEE])
        siren_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await siren_entity.async_turn_off()
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    send_result_success(client, message)


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, turn_on)
    register_api_command(server, turn_off)
