import asyncio
import logging

import aiohttp
from colorlog import ColoredFormatter

from zhawssclient.controller import Controller
from zhawssclient.model.commands import LightTurnOffCommand, LightTurnOnCommand

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

    test_lights = False
    test_switches = True
    waiter = asyncio.Future()
    controller = Controller("ws://localhost:8001/", aiohttp.ClientSession())
    await controller.connect()
    await controller.load_devices()

    devices = controller.devices

    for device in devices.values():
        _LOGGER.info("Device: %s", device)
        for entity in device.device.entities.values():
            _LOGGER.info("Entity: %s", entity)

    if test_lights:
        light_turn_on = LightTurnOnCommand.parse_obj(
            {
                "ieee": "b0:ce:18:14:03:09:c6:15",
                "unique_id": "b0:ce:18:14:03:09:c6:15-1",
            }
        )

        light_turn_off = LightTurnOffCommand.parse_obj(
            {
                "ieee": "b0:ce:18:14:03:09:c6:15",
                "unique_id": "b0:ce:18:14:03:09:c6:15-1",
            }
        )

        await controller.send_command(light_turn_off)

        await asyncio.sleep(3)

        await controller.send_command(light_turn_on)

        await asyncio.sleep(3)

        light_platform_entity = devices["b0:ce:18:14:03:09:c6:15"].device.entities[
            "b0:ce:18:14:03:09:c6:15-1"
        ]

        await controller.lights.turn_off(light_platform_entity)

        await asyncio.sleep(3)

        await controller.lights.turn_on(light_platform_entity)

        await asyncio.sleep(3)

    if test_switches:

        switch_platform_entity = devices["00:15:8d:00:02:82:d0:78"].device.entities[
            "00:15:8d:00:02:82:d0:78-1"
        ]

        await controller.switches.turn_off(switch_platform_entity)

        await asyncio.sleep(3)

        await controller.switches.turn_on(switch_platform_entity)

        await asyncio.sleep(3)

    await waiter


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
