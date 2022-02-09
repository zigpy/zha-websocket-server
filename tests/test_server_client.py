import os
import tempfile

import aiohttp
import pytest

from zhaws.client.client import Client
from zhaws.server.config.model import ServerConfiguration
from zhaws.server.websocket.server import Server


@pytest.fixture
def server_configuration() -> ServerConfiguration:
    port = aiohttp.test_utils.unused_port()
    with tempfile.TemporaryDirectory() as tempdir:
        # you can e.g. create a file here:
        config_path = os.path.join(tempdir, "configuration.json")
        server_config = ServerConfiguration.parse_obj(
            {
                "zigpy_configuration": {
                    "database_path": os.path.join(tempdir, "zigbee.db"),
                    "enable_quirks": True,
                },
                "radio_configuration": {
                    "type": "ezsp",
                    "path": "/dev/tty.SLAB_USBtoUART",
                    "baudrate": 115200,
                    "flow_control": "hardware",
                },
                "host": "localhost",
                "port": port,
                "network_auto_start": False,
            }
        )
        with open(config_path, "w") as tmpfile:
            tmpfile.write(server_config.json())
            return server_config


@pytest.fixture
async def connected_client_and_server(loop, server_configuration: ServerConfiguration):
    async with Server(configuration=server_configuration) as server:
        async with Client(f"ws://localhost:{server_configuration.port}") as client:
            yield client, server


async def test_server_client_connect_disconnect(
    server_configuration: ServerConfiguration,
):
    """Tests basic connect/disconnect logic."""

    async with Server(configuration=server_configuration) as server:
        assert server.is_serving
        assert server._ws_server is not None

        async with Client(f"ws://localhost:{server_configuration.port}") as client:
            assert client.connected
            assert "connected" in repr(client)

            # The client does not begin listening immediately
            assert client._listen_task is None
            await client.listen()
            assert client._listen_task is not None

        # The listen task is automatically stopped when we disconnect
        assert client._listen_task is None
        assert "not connected" in repr(client)
        assert not client.connected

    assert not server.is_serving
    assert server._ws_server is None


async def test_client_message_id_uniqueness(connected_client_and_server):
    """Tests that client message IDs are unique."""
    client, server = connected_client_and_server

    ids = [client.new_message_id() for _ in range(1000)]
    assert len(ids) == len(set(ids))


async def test_client_stop_server(connected_client_and_server):
    """Tests that the client can stop the server"""
    client, server = connected_client_and_server

    assert server.is_serving
    await client.async_send_command_no_wait({"command": "stop_server", "message_id": 1})
    await client.disconnect()
    await server.wait_closed()
    assert not server.is_serving
