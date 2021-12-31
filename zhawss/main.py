"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import json
import logging
from typing import Callable, Dict

from colorlog import ColoredFormatter
import uvloop
import voluptuous as vol
import websockets

from zhawss.application.controller import Controller
from zhawss.const import COMMAND, WEBSOCKET_API
from zhawss.websocket_api.decorators import MINIMAL_MESSAGE_SCHEMA

_LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    uvloop.install()
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    colorfmt = f"%(log_color)s{fmt}%(reset)s"
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().handlers[0].setFormatter(
        ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )
    )
    waiter = asyncio.Future()
    controller: Controller = Controller(waiter)

    async def handler(websocket):
        """Websocket handler."""

        async for message in websocket:

            handlers: Dict[str, Callable] = controller.data[WEBSOCKET_API]

            message = json.loads(message)
            _LOGGER.info("Received message on websocket: %s", message)

            try:
                msg = MINIMAL_MESSAGE_SCHEMA(message)
            except vol.Invalid:
                _LOGGER.error("Received invalid command", message)
                continue

            if msg[COMMAND] not in handlers:
                _LOGGER.error("Received invalid command: {}".format(msg[COMMAND]))
                continue

            handler, schema = handlers[msg[COMMAND]]

            try:
                handler(controller, websocket, schema(msg))
            except Exception as err:  # pylint: disable=broad-except
                # TODO Fix this
                websocket.async_handle_exception(msg, err)

    async def main():
        async with websockets.serve(handler, "", 8001, logger=_LOGGER):
            await waiter

    asyncio.get_event_loop().run_until_complete(main())
