"""Websocket application to run a zigpy Zigbee network."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from zhaws.server.config.model import ServerConfiguration
from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


async def main(config_path: str | None = None) -> None:
    """Run the websocket server."""
    if config_path is None:
        raise ValueError("config_path must be provided")
    else:
        _LOGGER.info("Loading configuration from %s", config_path)
        path = Path(config_path)
        configuration = ServerConfiguration.parse_file(path)
    async with Server(configuration=configuration) as server:
        await server.wait_closed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the ZHAWS server")
    parser.add_argument(
        "--config", type=str, default=None, help="Path to the configuration file"
    )

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

    asyncio.run(main(args.config))
