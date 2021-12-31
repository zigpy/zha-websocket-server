"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging

from colorlog import ColoredFormatter
import uvloop
import websockets

from zhawss.application.client import ClientManager
from zhawss.application.controller import Controller

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
    waiter: asyncio.Future = asyncio.Future()
    controller: Controller = Controller(waiter)
    client_manager: ClientManager = ClientManager(controller)

    async def main():
        async with websockets.serve(
            client_manager.add_client, "", 8001, logger=_LOGGER
        ):
            await waiter

    asyncio.get_event_loop().run_until_complete(main())
