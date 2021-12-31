"""Websocket api for zhawss."""

from typing import Union, cast

import voluptuous

from zhawss.const import WEBSOCKET_API
from zhawss.types import ControllerType

from . import decorators


def async_register_command(
    controller: ControllerType,
    command_or_handler: Union[str, decorators.WebSocketCommandHandler],
    handler: Union[decorators.WebSocketCommandHandler, None] = None,
    schema: Union[voluptuous.Schema, None] = None,
) -> None:
    """Register a websocket command."""
    # pylint: disable=protected-access
    if handler is None:
        handler = cast(decorators.WebSocketCommandHandler, command_or_handler)
        command = handler._ws_command  # type: ignore[attr-defined]
        schema = handler._ws_schema  # type: ignore[attr-defined]
    else:
        command = command_or_handler
    if (handlers := controller.data.get(WEBSOCKET_API)) is None:
        handlers = controller.data[WEBSOCKET_API] = {}
    handlers[command] = (handler, schema)
