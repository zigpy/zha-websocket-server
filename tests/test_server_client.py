import aiohttp
import pytest

from zhaws.client.client import Client
from zhaws.server.const import APICommands
from zhaws.server.websocket.server import Server


@pytest.fixture
async def connected_client_and_server(loop):
    port = aiohttp.test_utils.unused_port()

    async with Server(host="localhost", port=port) as server:
        async with Client(f"ws://localhost:{port}") as client:
            yield client, server


async def test_server_client_connect():
    port = aiohttp.test_utils.unused_port()

    async with Server(host="localhost", port=port) as server:
        repr(server)

        async with Client(f"ws://localhost:{port}") as client:
            assert "connected" in repr(client)

            assert client._listen_task is None
            await client.listen()
            assert client._listen_task is not None

            await client.async_send_command_no_wait(
                {"command": APICommands.GET_DEVICES}
            )

        assert client._listen_task is None
        assert "not connected" in repr(client)
