import aiohttp
import pytest

from zhaws.client.client import Client
from zhaws.server.websocket.server import Server


@pytest.fixture
async def connected_client_and_server(loop):
    port = aiohttp.test_utils.unused_port()

    async with Server(host="localhost", port=port) as server:
        async with Client(f"ws://localhost:{port}") as client:
            yield client, server


async def test_server_client_connect_disconnect():
    """Tests basic connect/disconnect logic."""
    port = aiohttp.test_utils.unused_port()

    async with Server(host="localhost", port=port) as server:
        assert server.is_serving
        assert server._ws_server is not None

        async with Client(f"ws://localhost:{port}") as client:
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
