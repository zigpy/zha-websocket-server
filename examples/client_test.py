import asyncio
import logging

import aiohttp
from colorlog import ColoredFormatter

from zhaws.client.controller import Controller
from zhaws.client.model.commands import LightTurnOffCommand, LightTurnOnCommand

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
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
    test_switches = False
    test_alarm_control_panel = False
    test_locks = False
    test_buttons = False
    waiter: asyncio.Future = asyncio.Future()
    controller = Controller("ws://localhost:8001/", aiohttp.ClientSession())
    await controller.connect()
    await controller.clients.listen()
    await controller.load_devices()
    await controller.load_groups()

    devices = controller.devices

    for device in devices.values():
        _LOGGER.info("Device: %s", device)
        for entity in device.device.entities.values():
            _LOGGER.info("Entity: %s", entity)

    groups = controller.groups
    for group in groups.values():
        _LOGGER.info("Group: %s", group)
        for entity in group.group.entities:
            _LOGGER.info("Entity: %s", entity)

    if test_lights:
        try:
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
        except Exception as err:
            _LOGGER.error(err)

    if test_switches:
        try:
            switch_platform_entity = devices["00:15:8d:00:02:82:d0:78"].device.entities[
                "00:15:8d:00:02:82:d0:78-1"
            ]

            _LOGGER.warning("Switch: %s", switch_platform_entity)

            await controller.switches.turn_off(switch_platform_entity)

            await asyncio.sleep(3)

            await controller.switches.turn_on(switch_platform_entity)

            await asyncio.sleep(3)

            await controller.entities.refresh_state(switch_platform_entity)

            await asyncio.sleep(3)
        except Exception as err:
            _LOGGER.error(err)

    if test_alarm_control_panel:

        try:
            alarm_control_panel_platform_entity = devices[
                "00:0d:6f:00:05:65:83:f2"
            ].device.entities["00:0d:6f:00:05:65:83:f2-1"]

            await controller.alarm_control_panels.trigger(
                alarm_control_panel_platform_entity
            )

            await asyncio.sleep(3)
        except Exception as err:
            _LOGGER.error(err)

    if test_locks:

        try:
            lock_platform_entity = devices["68:0a:e2:ff:fe:6a:22:af"].device.entities[
                "68:0a:e2:ff:fe:6a:22:af-1-257"
            ]

            await controller.locks.lock(lock_platform_entity)

            await asyncio.sleep(3)

            await controller.locks.unlock(lock_platform_entity)

            await asyncio.sleep(3)
        except Exception as err:
            _LOGGER.error(err)

    if test_buttons:

        try:
            button_platform_entity = devices["04:cf:8c:df:3c:7f:c5:a7"].device.entities[
                "04:cf:8c:df:3c:7f:c5:a7-1-3"
            ]

            await controller.buttons.press(button_platform_entity)

            await asyncio.sleep(3)
        except Exception as err:
            _LOGGER.error(err)

    """TODO turn this into an example for how to create a group with the client
    await controller.groups_helper.create_group(
        "test-lumi-group",
        members=[
            devices["00:15:8d:00:02:82:d0:78"].device.entities[
                "00:15:8d:00:02:82:d0:78-1"
            ],
            devices["00:15:8d:00:02:82:d3:0f"].device.entities[
                "00:15:8d:00:02:82:d3:0f-1"
            ],
        ],
    )
    """

    await waiter


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
