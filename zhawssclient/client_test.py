import asyncio

import aiohttp

from zhawssclient.controller import Controller
from zhawssclient.model.commands import GetDevicesResponse


async def main():
    async with aiohttp.ClientSession() as client:
        controller = Controller("ws://localhost:8001/", client)
        await controller.connect()

        response: GetDevicesResponse = await controller.get_devices()

        print("Devices: ", response)

        for device in response.devices.values():
            print("Device: ", device)
            for entity in device.entities.values():
                print("Entity: ", entity)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
