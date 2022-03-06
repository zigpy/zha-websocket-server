"""Test zha switch."""
import logging
from typing import Awaitable, Callable, Optional
from unittest.mock import MagicMock, call

import pytest
from slugify import slugify
from zigpy.device import Device as ZigpyDevice
import zigpy.profiles.zha
import zigpy.profiles.zha as zha
from zigpy.types.named import EUI64
import zigpy.zcl.clusters.general as general

from zhaws.client.controller import Controller
from zhaws.client.model.events import (
    DeviceJoinedEvent,
    DeviceLeftEvent,
    RawDeviceInitializedEvent,
)
from zhaws.client.model.types import BasePlatformEntity, SwitchEntity, SwitchGroupEntity
from zhaws.client.proxy import DeviceProxy, GroupProxy
from zhaws.server.const import ControllerEvents
from zhaws.server.platforms.registries import Platform
from zhaws.server.websocket.server import Server
from zhaws.server.zigbee.controller import DevicePairingStatus
from zhaws.server.zigbee.device import Device
from zhaws.server.zigbee.group import Group, GroupMemberReference

from .common import async_find_group_entity_id, find_entity_id
from .conftest import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE

ON = 1
OFF = 0
IEEE_GROUPABLE_DEVICE = "01:2d:6f:00:0a:90:69:e8"
IEEE_GROUPABLE_DEVICE2 = "02:2d:6f:00:0a:90:69:e8"
_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def zigpy_device(zigpy_device_mock: Callable[..., ZigpyDevice]) -> ZigpyDevice:
    """Device tracker zigpy device."""
    endpoints = {
        1: {
            SIG_EP_INPUT: [general.Basic.cluster_id, general.OnOff.cluster_id],
            SIG_EP_OUTPUT: [],
            SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH,
            SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID,
        }
    }
    return zigpy_device_mock(endpoints)


@pytest.fixture
async def device_switch_1(
    zigpy_device_mock: Callable[..., ZigpyDevice],
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
) -> Device:
    """Test zha switch platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [general.OnOff.cluster_id, general.Groups.cluster_id],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH,
                SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID,
            }
        },
        ieee=IEEE_GROUPABLE_DEVICE,
    )
    zha_device = await device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


def get_entity(zha_dev: DeviceProxy, entity_id: str) -> BasePlatformEntity:
    """Get entity."""
    entities = {
        entity.platform + "." + slugify(entity.name, separator="_"): entity
        for entity in zha_dev.device_model.entities.values()
    }
    return entities[entity_id]


def get_group_entity(
    group_proxy: GroupProxy, entity_id: str
) -> Optional[SwitchGroupEntity]:
    """Get entity."""
    entities = {
        entity.platform + "." + slugify(entity.name, separator="_"): entity
        for entity in group_proxy.group_model.entities.values()
    }

    return entities.get(entity_id)  # type: ignore


@pytest.fixture
async def device_switch_2(
    zigpy_device_mock: Callable[..., ZigpyDevice],
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
) -> Device:
    """Test zha switch platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [general.OnOff.cluster_id, general.Groups.cluster_id],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH,
                SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID,
            }
        },
        ieee=IEEE_GROUPABLE_DEVICE2,
    )
    zha_device = await device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


async def test_controller_devices(
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
    zigpy_device: ZigpyDevice,
    connected_client_and_server: tuple[Controller, Server],
) -> None:
    """Test client controller device related functionality."""
    controller, server = connected_client_and_server
    zha_device = await device_joined(zigpy_device)
    entity_id = find_entity_id(Platform.SWITCH, zha_device)
    assert entity_id is not None

    client_device: Optional[DeviceProxy] = controller.devices.get(zha_device.ieee)
    assert client_device is not None
    entity: SwitchEntity = get_entity(client_device, entity_id)  # type: ignore
    assert entity is not None

    assert isinstance(entity, SwitchEntity)

    assert entity.state.state is False

    await controller.load_devices()
    devices: dict[EUI64, DeviceProxy] = controller.devices
    assert len(devices) == 1
    assert zha_device.ieee in devices

    # test client -> server
    await controller.devices_helper.remove_device(client_device.device_model)
    assert server.controller.application_controller.remove.call_count == 1
    assert server.controller.application_controller.remove.call_args == call(
        client_device.device_model.ieee
    )

    # test server -> client
    server.controller.device_removed(zigpy_device)
    await server.block_till_done()
    assert len(controller.devices) == 0

    # rejoin the device
    zha_device = await device_joined(zigpy_device)
    await server.block_till_done()
    assert len(controller.devices) == 1

    # test rejoining the same device
    zha_device = await device_joined(zigpy_device)
    await server.block_till_done()
    assert len(controller.devices) == 1

    # test controller events
    listener = MagicMock()

    # test device joined
    controller.on_event(ControllerEvents.DEVICE_JOINED, listener)
    device_joined_event = DeviceJoinedEvent(
        pairing_status=DevicePairingStatus.PAIRED,
        ieee=zigpy_device.ieee,
        nwk=str(zigpy_device.nwk).lower(),
    )
    server.controller.device_joined(zigpy_device)
    await server.block_till_done()
    assert listener.call_count == 1
    assert listener.call_args == call(device_joined_event)

    # test device left
    listener.reset_mock()
    controller.on_event(ControllerEvents.DEVICE_LEFT, listener)
    server.controller.device_left(zigpy_device)
    await server.block_till_done()
    assert listener.call_count == 1
    assert listener.call_args == call(
        DeviceLeftEvent(
            ieee=zigpy_device.ieee,
            nwk=str(zigpy_device.nwk).lower(),
        )
    )

    # test raw  device initialized
    listener.reset_mock()
    controller.on_event(ControllerEvents.RAW_DEVICE_INITIALIZED, listener)
    server.controller.raw_device_initialized(zigpy_device)
    await server.block_till_done()
    assert listener.call_count == 1
    assert listener.call_args == call(
        RawDeviceInitializedEvent(
            pairing_status=DevicePairingStatus.INTERVIEW_COMPLETE,
            ieee=zigpy_device.ieee,
            nwk=str(zigpy_device.nwk).lower(),
            manufacturer=client_device.device_model.manufacturer,
            model=client_device.device_model.model,
            signature=client_device.device_model.signature,
        )
    )


async def test_controller_groups(
    device_switch_1: Device,
    device_switch_2: Device,
    connected_client_and_server: tuple[Controller, Server],
) -> None:
    """Test client controller group related functionality."""
    controller, server = connected_client_and_server
    member_ieee_addresses = [device_switch_1.ieee, device_switch_2.ieee]
    members = [
        GroupMemberReference(ieee=device_switch_1.ieee, endpoint_id=1),
        GroupMemberReference(ieee=device_switch_2.ieee, endpoint_id=1),
    ]

    # test creating a group with 2 members
    zha_group: Group = await server.controller.async_create_zigpy_group(
        "Test Group", members
    )
    await server.block_till_done()

    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None

    entity_id = async_find_group_entity_id(Platform.SWITCH, zha_group)
    assert entity_id is not None

    group_proxy: Optional[GroupProxy] = controller.groups.get(2)
    assert group_proxy is not None

    entity: SwitchGroupEntity = get_group_entity(group_proxy, entity_id)  # type: ignore
    assert entity is not None

    assert isinstance(entity, SwitchGroupEntity)

    assert entity is not None

    await controller.load_groups()
    groups: dict[int, GroupProxy] = controller.groups
    # the application controller mock starts with a group already created
    assert len(groups) == 2
    assert zha_group.group_id in groups

    # test client -> server
    await controller.groups_helper.remove_groups([group_proxy.group_model])
    await server.block_till_done()
    assert len(controller.groups) == 1
