"""Websocket application to run a zigpy Zigbee network."""

import asyncio
import logging

from bellows.zigbee.application import ControllerApplication
from serial.serialutil import SerialException
import websockets


async def main():
    _LOGGER = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    waiter = asyncio.Future()

    async def handler(websocket):
        async for message in websocket:
            print(message)
            if message == "start":
                app_config = {}
                app_config["database_path"] = "./zigbee.db"
                app_config["device"] = {
                    "path": "/dev/cu.GoControl_zigbee\u0011",
                    "flow_control": "software",
                    "baudrate": 57600,
                }
                app_config = ControllerApplication.SCHEMA(app_config)
                try:
                    application_controller = await ControllerApplication.new(
                        app_config, auto_form=True, start_radio=True
                    )
                except (asyncio.TimeoutError, SerialException, OSError) as exception:
                    _LOGGER.error(
                        "Couldn't start %s coordinator",
                        "/dev/cu.GoControl_zigbee\u0011",
                        exc_info=exception,
                    )
            if message == "stop":
                await application_controller.pre_shutdown()
                waiter.set_result(True)

    async with websockets.serve(handler, "", 8001, logger=_LOGGER):
        await waiter  # run forever


if __name__ == "__main__":
    asyncio.run(main())
