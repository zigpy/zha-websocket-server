"""Decorators for the Websocket API."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

import voluptuous as vol

from zhawss.const import COMMAND, MINIMAL_MESSAGE_SCHEMA
from zhawss.types import (
    AsyncWebSocketCommandHandler,
    ClientType,
    ServerType,
    WebSocketCommandHandler,
)

POSITIVE_INT = vol.All(vol.Coerce(int), vol.Range(min=0))


async def _handle_async_response(
    func: AsyncWebSocketCommandHandler,
    server: ServerType,
    client: ClientType,
    msg: dict[str, Any],
) -> None:
    """Create a response and handle exception."""
    try:
        await func(server, client, msg)
    except Exception as err:  # pylint: disable=broad-except
        # TODO fix this
        client.async_handle_exception(msg, err)


def async_response(
    func: AsyncWebSocketCommandHandler,
) -> WebSocketCommandHandler:
    """Decorate an async function to handle WebSocket API messages."""

    @wraps(func)
    def schedule_handler(
        server: ServerType, client: ClientType, msg: dict[str, Any]
    ) -> None:
        """Schedule the handler."""
        # As the webserver is now started before the start
        # event we do not want to block for websocket responders
        asyncio.create_task(_handle_async_response(func, server, client, msg))

    return schedule_handler


def websocket_command(
    schema: dict[vol.Marker, Any],
) -> Callable[[WebSocketCommandHandler], WebSocketCommandHandler]:
    """Tag a function as a websocket command."""
    command = schema[COMMAND]

    def decorate(func: WebSocketCommandHandler) -> WebSocketCommandHandler:
        """Decorate ws command function."""
        # pylint: disable=protected-access
        func._ws_schema = MINIMAL_MESSAGE_SCHEMA.extend(schema)  # type: ignore[attr-defined]
        func._ws_command = command  # type: ignore[attr-defined]
        return func

    return decorate
