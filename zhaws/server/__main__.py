"""Websocket application to run a zigpy Zigbee network."""

import argparse
import asyncio
import logging

from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


async def main(host: str, port: int) -> None:
    async with Server(host=host, port=port) as server:
        await server.wait_closed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the ZHAWS server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8001, help="Bind port")

    args = parser.parse_args()

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

    asyncio.run(main(args.host, args.port))
