"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging

from colorlog import ColoredFormatter
import uvloop

_LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    uvloop.install()
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
    colorfmt = f"%(log_color)s{fmt}%(reset)s"
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().handlers[0].setFormatter(
        ColoredFormatter(
            colorfmt,
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
        from zhawss.websocket.server import Server

        await Server().start_server()

    asyncio.get_event_loop().run_until_complete(main())
