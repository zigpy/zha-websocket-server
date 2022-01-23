"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging

from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    async with Server(host="0.0.0.0", port=8001):
        await asyncio.Future()  # wait forever


if __name__ == "__main__":
    import uvloop

    uvloop.install()

    from colorlog import ColoredFormatter

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

    asyncio.run(main())
