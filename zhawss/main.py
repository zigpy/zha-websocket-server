"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging

from colorlog import ColoredFormatter
import uvloop

from zhawss.server import Server

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

    async def main():
        await Server().start_server()

    asyncio.get_event_loop().run_until_complete(main())
