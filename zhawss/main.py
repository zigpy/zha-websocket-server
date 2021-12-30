"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging
from typing import Callable, Dict

from application.controller import Controller
import uvloop
import websockets

HANDLERS: Dict[str, Callable] = {}


if __name__ == "__main__":
    uvloop.install()
    _LOGGER = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    waiter = asyncio.Future()
    app_config = {}
    app_config["database_path"] = "./zigbee.db"
    app_config["device"] = {
        "path": "/dev/cu.GoControl_zigbee\u0011",
        "flow_control": "software",
        "baudrate": 57600,
    }

    async def handler(websocket):
        controller: Controller = Controller(websocket)
        async for message in websocket:
            print(message)
            if message == "start":
                await controller.start_network(app_config)
            if message == "stop":
                await controller.stop_network()
                waiter.set_result(True)

    async def main():
        async with websockets.serve(handler, "", 8001, logger=_LOGGER):
            await waiter

    asyncio.get_event_loop().run_until_complete(main())
