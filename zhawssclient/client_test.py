import asyncio
import logging

import aiohttp
from colorlog import ColoredFormatter

from zhawssclient.controller import Controller

_LOGGER = logging.getLogger(__name__)


async def main():
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

    waiter = asyncio.Future()
    controller = Controller("ws://localhost:8001/", aiohttp.ClientSession())
    await controller.connect()
    await controller.load_devices()

    devices = controller.devices

    for device in devices.values():
        _LOGGER.info("Device: %s", device)
        for entity in device.device.entities.values():
            _LOGGER.info("Entity: %s", entity)

    await waiter


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
