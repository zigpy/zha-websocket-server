"""Test configuration for the ZHA component."""

from asyncio import AbstractEventLoop
from collections.abc import AsyncGenerator, Callable
import itertools
import logging
import os
import tempfile
import time
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
import zigpy
from zigpy.application import ControllerApplication
import zigpy.config
from zigpy.const import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
import zigpy.device
import zigpy.group
import zigpy.profiles
import zigpy.types
from zigpy.zcl.clusters.general import Basic, Groups
from zigpy.zcl.foundation import Status
import zigpy.zdo.types as zdo_t

from tests import common
from zha.zigbee.device import Device
from zhaws.client.controller import Controller
from zhaws.server.config.model import ServerConfiguration
from zhaws.server.websocket.server import Server

FIXTURE_GRP_ID = 0x1001
FIXTURE_GRP_NAME = "fixture group"
COUNTER_NAMES = ["counter_1", "counter_2", "counter_3"]
_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def server_configuration() -> ServerConfiguration:
    """Server configuration fixture."""
    port = aiohttp.test_utils.unused_port()
    with tempfile.TemporaryDirectory() as tempdir:
        # you can e.g. create a file here:
        config_path = os.path.join(tempdir, "configuration.json")
        server_config = ServerConfiguration.parse_obj(
            {
                "host": "localhost",
                "port": port,
                "network_auto_start": False,
                "zha_config": {
                    "coordinator_configuration": {
                        "path": "/dev/cu.wchusbserial971207DO",
                        "baudrate": 115200,
                        "flow_control": "hardware",
                        "radio_type": "ezsp",
                    },
                    "quirks_configuration": {
                        "enabled": True,
                        "custom_quirks_path": "/Users/davidmulcahey/.homeassistant/quirks",
                    },
                    "device_overrides": {},
                    "light_options": {
                        "default_light_transition": 0.0,
                        "enable_enhanced_light_transition": False,
                        "enable_light_transitioning_flag": True,
                        "always_prefer_xy_color_mode": True,
                        "group_members_assume_state": True,
                    },
                    "device_options": {
                        "enable_identify_on_join": True,
                        "consider_unavailable_mains": 5,
                        "consider_unavailable_battery": 21600,
                        "enable_mains_startup_polling": True,
                    },
                    "alarm_control_panel_options": {
                        "master_code": "1234",
                        "failed_tries": 3,
                        "arm_requires_code": False,
                    },
                },
                "zigpy_config": {
                    "startup_energy_scan": False,
                    "handle_unknown_devices": True,
                    "source_routing": True,
                    "max_concurrent_requests": 128,
                    "ezsp_config": {
                        "CONFIG_PACKET_BUFFER_COUNT": 255,
                        "CONFIG_MTORR_FLOW_CONTROL": 1,
                        "CONFIG_KEY_TABLE_SIZE": 12,
                        "CONFIG_ROUTE_TABLE_SIZE": 200,
                    },
                    "ota": {
                        "otau_directory": "/Users/davidmulcahey/.homeassistant/zigpy_ota",
                        "inovelli_provider": False,
                        "thirdreality_provider": True,
                    },
                    "database_path": os.path.join(tempdir, "zigbee.db"),
                    "device": {
                        "baudrate": 115200,
                        "flow_control": "hardware",
                        "path": "/dev/cu.wchusbserial971207DO",
                    },
                },
            }
        )
        with open(config_path, "w") as tmpfile:
            tmpfile.write(server_config.json())
            return server_config


class _FakeApp(ControllerApplication):
    async def add_endpoint(self, descriptor: zdo_t.SimpleDescriptor):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def force_remove(self, dev: zigpy.device.Device):
        pass

    async def load_network_info(self, *, load_devices: bool = False):
        pass

    async def permit_ncp(self, time_s: int = 60):
        pass

    async def permit_with_link_key(
        self, node: zigpy.types.EUI64, link_key: zigpy.types.KeyData, time_s: int = 60
    ):
        pass

    async def reset_network_info(self):
        pass

    async def send_packet(self, packet: zigpy.types.ZigbeePacket):
        pass

    async def start_network(self):
        pass

    async def write_network_info(
        self, *, network_info: zigpy.state.NetworkInfo, node_info: zigpy.state.NodeInfo
    ) -> None:
        pass

    async def request(
        self,
        device: zigpy.device.Device,
        profile: zigpy.types.uint16_t,
        cluster: zigpy.types.uint16_t,
        src_ep: zigpy.types.uint8_t,
        dst_ep: zigpy.types.uint8_t,
        sequence: zigpy.types.uint8_t,
        data: bytes,
        *,
        expect_reply: bool = True,
        use_ieee: bool = False,
        extended_timeout: bool = False,
    ):
        pass

    async def move_network_to_channel(
        self, new_channel: int, *, num_broadcasts: int = 5
    ) -> None:
        pass


@pytest.fixture
async def zigpy_app_controller() -> AsyncGenerator[ControllerApplication, None]:
    """Zigpy ApplicationController fixture."""
    with tempfile.TemporaryDirectory() as tempdir:
        app = _FakeApp(
            {
                zigpy.config.CONF_DATABASE: os.path.join(tempdir, "zigbee.db"),
                zigpy.config.CONF_DEVICE: {zigpy.config.CONF_DEVICE_PATH: "/dev/null"},
                zigpy.config.CONF_STARTUP_ENERGY_SCAN: False,
                zigpy.config.CONF_NWK_BACKUP_ENABLED: False,
                zigpy.config.CONF_TOPO_SCAN_ENABLED: False,
                zigpy.config.CONF_OTA: {
                    zigpy.config.CONF_OTA_ENABLED: False,
                },
            }
        )
        app.groups.add_group(FIXTURE_GRP_ID, FIXTURE_GRP_NAME, suppress_event=True)

        app.state.node_info.nwk = 0x0000
        app.state.node_info.ieee = zigpy.types.EUI64.convert("00:15:8d:00:02:32:4f:32")
        app.state.network_info.pan_id = 0x1234
        app.state.network_info.extended_pan_id = app.state.node_info.ieee
        app.state.network_info.channel = 15
        app.state.network_info.network_key.key = zigpy.types.KeyData(range(16))
        app.state.counters = zigpy.state.CounterGroups()
        app.state.counters["ezsp_counters"] = zigpy.state.CounterGroup("ezsp_counters")
        for name in COUNTER_NAMES:
            app.state.counters["ezsp_counters"][name].increment()

        # Create a fake coordinator device
        dev = app.add_device(nwk=app.state.node_info.nwk, ieee=app.state.node_info.ieee)
        dev.node_desc = zdo_t.NodeDescriptor()
        dev.node_desc.logical_type = zdo_t.LogicalType.Coordinator
        dev.manufacturer = "Coordinator Manufacturer"
        dev.model = "Coordinator Model"

        ep = dev.add_endpoint(1)
        ep.add_input_cluster(Basic.cluster_id)
        ep.add_input_cluster(Groups.cluster_id)

        with patch("zigpy.device.Device.request", return_value=[Status.SUCCESS]):
            yield app


@pytest.fixture
async def connected_client_and_server(
    event_loop: AbstractEventLoop,
    server_configuration: ServerConfiguration,
    zigpy_app_controller: ControllerApplication,
) -> AsyncGenerator[tuple[Controller, Server], None]:
    """Return the connected client and server fixture."""

    application_controller_patch = patch(
        "bellows.zigbee.application.ControllerApplication.new",
        return_value=zigpy_app_controller,
    )

    with application_controller_patch:
        async with Server(configuration=server_configuration) as server:
            await server.controller.start_network()
            async with Controller(
                f"ws://localhost:{server_configuration.port}"
            ) as controller:
                await controller.clients.listen()
                yield controller, server


@pytest.fixture
def device_joined(
    connected_client_and_server: tuple[Controller, Server],
) -> Callable[[zigpy.device.Device], Device]:
    """Return a newly joined ZHAWS device."""

    async def _zha_device(zigpy_dev: zigpy.device.Device) -> Device:
        client, server = connected_client_and_server
        await server.controller.gateway.async_device_initialized(zigpy_dev)
        await server.block_till_done()
        return server.controller.gateway.get_device(zigpy_dev.ieee)

    return _zha_device


@pytest.fixture
def cluster_handler() -> Callable:
    """Clueter handler mock factory fixture."""

    def cluster_handler(name: str, cluster_id: int, endpoint_id: int = 1) -> MagicMock:
        ch = MagicMock()
        ch.name = name
        ch.generic_id = f"channel_0x{cluster_id:04x}"
        ch.id = f"{endpoint_id}:0x{cluster_id:04x}"
        ch.async_configure = AsyncMock()
        ch.async_initialize = AsyncMock()
        return ch

    return cluster_handler


@pytest.fixture
def zigpy_device_mock(
    zigpy_app_controller: ControllerApplication,
) -> Callable[..., zigpy.device.Device]:
    """Make a fake device using the specified cluster classes."""

    def _mock_dev(
        endpoints: dict[int, dict[str, Any]],
        ieee: str = "00:0d:6f:00:0a:90:69:e7",
        manufacturer: str = "FakeManufacturer",
        model: str = "FakeModel",
        node_descriptor: bytes = b"\x02@\x807\x10\x7fd\x00\x00*d\x00\x00",
        nwk: int = 0xB79C,
        patch_cluster: bool = True,
        quirk: Optional[Callable] = None,
    ) -> zigpy.device.Device:
        """Make a fake device using the specified cluster classes."""
        device = zigpy.device.Device(
            zigpy_app_controller, zigpy.types.EUI64.convert(ieee), nwk
        )
        device.manufacturer = manufacturer
        device.model = model
        device.node_desc = zdo_t.NodeDescriptor.deserialize(node_descriptor)[0]
        device.last_seen = time.time()

        for epid, ep in endpoints.items():
            endpoint = device.add_endpoint(epid)
            endpoint.device_type = ep[SIG_EP_TYPE]
            endpoint.profile_id = ep.get(SIG_EP_PROFILE)
            endpoint.request = AsyncMock(return_value=[0])

            for cluster_id in ep.get(SIG_EP_INPUT, []):
                endpoint.add_input_cluster(cluster_id)

            for cluster_id in ep.get(SIG_EP_OUTPUT, []):
                endpoint.add_output_cluster(cluster_id)

        if quirk:
            device = quirk(zigpy_app_controller, device.ieee, device.nwk, device)

        if patch_cluster:
            for endpoint in (ep for epid, ep in device.endpoints.items() if epid):
                endpoint.request = AsyncMock(return_value=[0])
                for cluster in itertools.chain(
                    endpoint.in_clusters.values(), endpoint.out_clusters.values()
                ):
                    common.patch_cluster(cluster)

        return device

    return _mock_dev
