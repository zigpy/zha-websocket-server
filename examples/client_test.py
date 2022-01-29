import asyncio
import logging

from colorlog import ColoredFormatter

from zhaws.client.controller import Controller
from zhaws.client.model.commands import (
    LightTurnOffCommand,
    LightTurnOnCommand,
    ReadClusterAttributesResponse,
)

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    test_lights = False
    test_switches = False
    test_alarm_control_panel = False
    test_locks = False
    test_buttons = False
    test_attributes = False
    test_stop_network = True

    async with Controller("ws://localhost:8001/") as controller:
        await controller.clients.listen()

        await controller.network.start_network(
            {
                "radio_type": "ezsp",
                "device": {
                    "path": "/dev/cu.GoControl_zigbee\u0011",
                    "flow_control": "software",
                    "baudrate": 57600,
                },
                "database_path": "./zigbee.db",
                "enable_quirks": True,
                "message_id": 1,
            }
        )

        await controller.load_devices()
        await controller.load_groups()

        devices = controller.devices

        for device in devices.values():
            _LOGGER.info("Device: %s", device)
            for entity in device.device_model.entities.values():
                _LOGGER.info("Entity: %s", entity)

        groups = controller.groups
        for group in groups.values():
            _LOGGER.info("Group: %s", group)
            for group_entity in group.group_model.entities.values():
                _LOGGER.info("Entity: %s", group_entity)

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

                light_platform_entity = devices[
                    "b0:ce:18:14:03:09:c6:15"
                ].device_model.entities["b0:ce:18:14:03:09:c6:15-1"]

                await controller.lights.turn_off(light_platform_entity)

                await asyncio.sleep(3)

                await controller.lights.turn_on(light_platform_entity)

                await asyncio.sleep(3)
            except Exception as err:
                _LOGGER.error(err)

        if test_switches:
            try:
                switch_platform_entity = devices[
                    "00:15:8d:00:02:82:d0:78"
                ].device_model.entities["00:15:8d:00:02:82:d0:78-1"]

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
                ].device_model.entities["00:0d:6f:00:05:65:83:f2-1"]

                await controller.alarm_control_panels.trigger(
                    alarm_control_panel_platform_entity
                )

                await asyncio.sleep(3)
            except Exception as err:
                _LOGGER.error(err)

        if test_locks:

            try:
                lock_platform_entity = devices[
                    "68:0a:e2:ff:fe:6a:22:af"
                ].device_model.entities["68:0a:e2:ff:fe:6a:22:af-1-257"]

                await controller.locks.lock(lock_platform_entity)

                await asyncio.sleep(3)

                await controller.locks.unlock(lock_platform_entity)

                await asyncio.sleep(3)
            except Exception as err:
                _LOGGER.error(err)

        if test_buttons:

            try:
                button_platform_entity = devices[
                    "04:cf:8c:df:3c:7f:c5:a7"
                ].device_model.entities["04:cf:8c:df:3c:7f:c5:a7-1-3"]

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
        if test_attributes:
            device = devices["00:15:8d:00:02:82:d0:78"]
            response: ReadClusterAttributesResponse = (
                await controller.devices_helper.read_cluster_attributes(
                    device.device_model, 0, "in", 1, ["date_code"]
                )
            )
            _LOGGER.warning("Read cluster attributes response: %s", response.dict())

            write_response = await controller.devices_helper.write_cluster_attribute(
                device.device_model, 0, "in", 1, "location_desc", "test location"
            )
            _LOGGER.warning(
                "Write cluster attribute response: %s", write_response.dict()
            )

        if test_stop_network:
            await controller.network.stop_network()
            await controller.server_helper.stop_server()

        await asyncio.Future()


if __name__ == "__main__":
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
