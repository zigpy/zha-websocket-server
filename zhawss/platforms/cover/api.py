"""WS API for the cover platform entity."""

# open, close, set position, stop


from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.const import COMMAND, IEEE, MESSAGE_ID
from zhawss.platforms.cover import ATTR_POSITION
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType
from zhawss.zigbee.device import ATTR_UNIQUE_ID


class CoverCommands(StrEnum):
    """Cover commands."""

    OPEN = "cover_open"
    CLOSE = "cover_close"
    SET_POSITION = "cover_set_position"
    STOP = "cover_stop"


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): CoverCommands.OPEN,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def open(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Open the cover."""
    try:
        device = server.controller.get_device(message[IEEE])
        cover_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await cover_entity.async_open_cover(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: CoverCommands.OPEN,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): CoverCommands.CLOSE,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def close(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Close the cover."""
    try:
        device = server.controller.get_device(message[IEEE])
        cover_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await cover_entity.async_close_cover(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: CoverCommands.CLOSE,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): CoverCommands.SET_POSITION,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
        vol.Required(ATTR_POSITION): int,
    }
)
async def set_position(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Set the cover position."""
    try:
        device = server.controller.get_device(message[IEEE])
        cover_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await cover_entity.async_set_cover_position(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: CoverCommands.SET_POSITION,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


@decorators.async_response
@decorators.websocket_command(
    {
        vol.Required(COMMAND): CoverCommands.STOP,
        vol.Required(IEEE): str,
        vol.Required(ATTR_UNIQUE_ID): str,
    }
)
async def stop(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Stop the cover."""
    try:
        device = server.controller.get_device(message[IEEE])
        cover_entity = device.get_platform_entity(message[ATTR_UNIQUE_ID])
    except ValueError as err:
        client.send_error(message[MESSAGE_ID], str(err))
        return

    try:
        await cover_entity.async_stop_cover(**message)
    except Exception as err:
        client.send_error(message[MESSAGE_ID], str(err))

    client.send_result_success(
        message[MESSAGE_ID],
        {
            COMMAND: CoverCommands.STOP,
            IEEE: message[IEEE],
            ATTR_UNIQUE_ID: message[ATTR_UNIQUE_ID],
        },
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, open)
    register_api_command(server, close)
    register_api_command(server, set_position)
    register_api_command(server, stop)
