"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import json
import logging
from typing import Callable, Dict

from application.controller import Controller
import uvloop
import websockets

from zhawss.const import COMMAND, COMMAND_START_NETWORK, COMMAND_STOP_NETWORK

HANDLERS: Dict[str, Callable] = {}
_LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    uvloop.install()
    logging.basicConfig(level=logging.DEBUG)
    waiter = asyncio.Future()
    controller: Controller = Controller(waiter)

    async def handler(websocket):
        """Websocket handler."""

        # maybe use a decorator to do this somehow
        HANDLERS[COMMAND_START_NETWORK] = controller.start_network
        HANDLERS[COMMAND_STOP_NETWORK] = controller.stop_network

        async for message in websocket:
            message = json.loads(message)
            _LOGGER.info("received websocket message: %s", message)
            await HANDLERS[message[COMMAND]](message)

    async def main():
        async with websockets.serve(handler, "", 8001, logger=_LOGGER):
            await waiter

    asyncio.get_event_loop().run_until_complete(main())
