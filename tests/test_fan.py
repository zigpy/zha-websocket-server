"""Test zha fan."""
import asyncio
import logging
from typing import Awaitable, Callable, Optional
from unittest.mock import call

import pytest
from slugify import slugify
from zigpy.device import Device as ZigpyDevice
import zigpy.profiles.zha as zha
import zigpy.zcl.clusters.general as general
import zigpy.zcl.clusters.hvac as hvac

from zhaws.client.controller import Controller
from zhaws.client.model.types import FanEntity, FanGroupEntity
from zhaws.client.proxy import DeviceProxy, GroupProxy
from zhaws.server.platforms.fan import PRESET_MODE_ON, SPEED_HIGH
from zhaws.server.platforms.registries import Platform
from zhaws.server.websocket.server import Server
from zhaws.server.zigbee.device import Device

from .common import find_entity_id, send_attributes_report
from .conftest import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE

IEEE_GROUPABLE_DEVICE = "01:2d:6f:00:0a:90:69:e8"
IEEE_GROUPABLE_DEVICE2 = "02:2d:6f:00:0a:90:69:e8"

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def zigpy_device(
    zigpy_device_mock: Callable[..., ZigpyDevice],
) -> ZigpyDevice:
    """Device tracker zigpy device."""
    endpoints = {
        1: {
            SIG_EP_INPUT: [hvac.Fan.cluster_id],
            SIG_EP_OUTPUT: [],
            SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH,
            SIG_EP_PROFILE: zha.PROFILE_ID,
        }
    }
    return zigpy_device_mock(
        endpoints, node_descriptor=b"\x02@\x8c\x02\x10RR\x00\x00\x00R\x00\x00"
    )


@pytest.fixture
async def coordinator(
    zigpy_device_mock: Callable[..., ZigpyDevice],
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
) -> Device:
    """Test zha fan platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [general.Groups.cluster_id],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT,
                SIG_EP_PROFILE: zha.PROFILE_ID,
            }
        },
        ieee="00:15:8d:00:02:32:4f:32",
        nwk=0x0000,
        node_descriptor=b"\xf8\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",
    )
    zha_device = await device_joined(zigpy_device)
    await asyncio.sleep(0.001)
    zha_device.available = True
    return zha_device


@pytest.fixture
async def device_fan_1(
    zigpy_device_mock: Callable[..., ZigpyDevice],
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
) -> Device:
    """Test zha fan platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [
                    general.Groups.cluster_id,
                    general.OnOff.cluster_id,
                    hvac.Fan.cluster_id,
                ],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.ON_OFF_LIGHT,
                SIG_EP_PROFILE: zha.PROFILE_ID,
            },
        },
        ieee=IEEE_GROUPABLE_DEVICE,
    )
    zha_device = await device_joined(zigpy_device)
    await asyncio.sleep(0.001)
    zha_device.available = True
    return zha_device


@pytest.fixture
async def device_fan_2(
    zigpy_device_mock: Callable[..., ZigpyDevice],
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
) -> Device:
    """Test zha fan platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [
                    general.Groups.cluster_id,
                    general.OnOff.cluster_id,
                    hvac.Fan.cluster_id,
                    general.LevelControl.cluster_id,
                ],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.ON_OFF_LIGHT,
                SIG_EP_PROFILE: zha.PROFILE_ID,
            },
        },
        ieee=IEEE_GROUPABLE_DEVICE2,
    )
    zha_device = await device_joined(zigpy_device)
    await asyncio.sleep(0.001)
    zha_device.available = True
    return zha_device


def get_entity(zha_dev: DeviceProxy, entity_id: str) -> FanEntity:
    """Get entity."""
    entities = {
        entity.platform + "." + slugify(entity.name, separator="_"): entity
        for entity in zha_dev.device_model.entities.values()
    }
    return entities[entity_id]  # type: ignore


def get_group_entity(
    group_proxy: GroupProxy, entity_id: str
) -> Optional[FanGroupEntity]:
    """Get entity."""
    entities = {
        entity.platform + "." + slugify(entity.name, separator="_"): entity
        for entity in group_proxy.group_model.entities.values()
    }

    return entities.get(entity_id)  # type: ignore


async def test_fan(
    device_joined: Callable[[ZigpyDevice], Awaitable[Device]],
    zigpy_device: ZigpyDevice,
    connected_client_and_server: tuple[Controller, Server],
) -> None:
    """Test zha fan platform."""
    controller, server = connected_client_and_server
    zha_device = await device_joined(zigpy_device)
    await asyncio.sleep(0.001)
    cluster = zigpy_device.endpoints.get(1).fan
    entity_id = find_entity_id(Platform.FAN, zha_device)
    assert entity_id is not None

    client_device: Optional[DeviceProxy] = controller.devices.get(str(zha_device.ieee))
    assert client_device is not None
    entity = get_entity(client_device, entity_id)
    assert entity is not None
    assert entity.state.is_on is False

    # turn on at fan
    await send_attributes_report(cluster, {1: 2, 0: 1, 2: 3})
    assert entity.state.is_on is True

    # turn off at fan
    await send_attributes_report(cluster, {1: 1, 0: 0, 2: 2})
    assert entity.state.is_on is False

    # turn on from client
    cluster.write_attributes.reset_mock()
    await async_turn_on(entity, controller)
    assert len(cluster.write_attributes.mock_calls) == 1
    assert cluster.write_attributes.call_args == call({"fan_mode": 2})

    # turn off from client
    cluster.write_attributes.reset_mock()
    await async_turn_off(entity, controller)
    assert len(cluster.write_attributes.mock_calls) == 1
    assert cluster.write_attributes.call_args == call({"fan_mode": 0})

    # change speed from client
    cluster.write_attributes.reset_mock()
    await async_set_speed(entity, controller, speed=SPEED_HIGH)
    assert len(cluster.write_attributes.mock_calls) == 1
    assert cluster.write_attributes.call_args == call({"fan_mode": 3})

    # change preset_mode from client
    cluster.write_attributes.reset_mock()
    await async_set_preset_mode(entity, controller, preset_mode=PRESET_MODE_ON)
    assert len(cluster.write_attributes.mock_calls) == 1
    assert cluster.write_attributes.call_args == call({"fan_mode": 4})

    """TODO need to return errors to client and assert against response
    # set invalid preset_mode from client
    cluster.write_attributes.reset_mock()
    with pytest.raises(NotValidPresetModeError):
        await async_set_preset_mode(
            entity, controller, preset_mode="invalid does not exist"
        )
    assert len(cluster.write_attributes.mock_calls) == 0
    """


async def async_turn_on(
    entity: FanEntity, controller: Controller, speed: Optional[str] = None
) -> None:
    """Turn fan on."""
    await controller.fans.turn_on(entity, speed=speed)
    await asyncio.sleep(0.001)


async def async_turn_off(entity: FanEntity, controller: Controller) -> None:
    """Turn fan off."""
    await controller.fans.turn_off(entity)
    await asyncio.sleep(0.001)


async def async_set_speed(
    entity: FanEntity, controller: Controller, speed: Optional[str] = None
) -> None:
    """Set speed for specified fan."""
    await controller.fans.turn_on(entity, speed=speed)
    await asyncio.sleep(0.001)


async def async_set_preset_mode(
    entity: FanEntity, controller: Controller, preset_mode: Optional[str] = None
) -> None:
    """Set preset_mode for specified fan."""
    assert preset_mode is not None
    await controller.fans.set_fan_preset_mode(entity, preset_mode)
    await asyncio.sleep(0.001)


"""
@patch(
    "zigpy.zcl.clusters.hvac.Fan.write_attributes",
    new=AsyncMock(return_value=zcl_f.WriteAttributesResponse.deserialize(b"\x00")[0]),
)
async def test_zha_group_fan_entity(device_fan_1, device_fan_2, coordinator):
    #Test the fan entity for a ZHA group.
    zha_gateway = get_zha_gateway(hass)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_fan_1._zha_gateway = zha_gateway
    device_fan_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_fan_1.ieee, device_fan_2.ieee]
    members = [
        GroupMemberReference(device_fan_1.ieee, 1),
        GroupMemberReference(device_fan_2.ieee, 1),
    ]

    # test creating a group with 2 members
    zha_group = await zha_gateway.async_create_zigpy_group("Test Group", members)
    asyncio.sleep(0.001)

    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None

    entity_domains = GROUP_PROBE.determine_entity_domains(zha_group)
    assert len(entity_domains) == 2

    assert Platform.LIGHT in entity_domains
    assert Platform.FAN in entity_domains

    entity_id = async_find_group_entity_id(Platform.FAN, zha_group)
    assert hass.states.get(entity_id) is not None

    group_fan_cluster = zha_group.endpoint[hvac.Fan.cluster_id]

    dev1_fan_cluster = device_fan_1.device.endpoints[1].fan
    dev2_fan_cluster = device_fan_2.device.endpoints[1].fan

    await async_enable_traffic([device_fan_1, device_fan_2], enabled=False)
    await async_wait_for_updates(hass)
    # test that the fans were created and that they are unavailable
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # allow traffic to flow through the gateway and device
    await async_enable_traffic([device_fan_1, device_fan_2])
    await async_wait_for_updates(hass)
    # test that the fan group entity was created and is off
    assert hass.states.get(entity_id).state is False

    # turn on from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_turn_on(entity_id)
    asyncio.sleep(0.001)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 2}

    # turn off from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_turn_off(entity_id)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 0}

    # change speed from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_set_speed(entity_id, speed=fan.SPEED_HIGH)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 3}

    # change preset mode from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_set_preset_mode(entity_id, preset_mode=PRESET_MODE_ON)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 4}

    # change preset mode from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_set_preset_mode(entity_id, preset_mode=PRESET_MODE_AUTO)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 5}

    # change preset mode from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_set_preset_mode(entity_id, preset_mode=PRESET_MODE_SMART)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 6}

    # test some of the group logic to make sure we key off states correctly
    await send_attributes_report(dev1_fan_cluster, {0: 0})
    await send_attributes_report(dev2_fan_cluster, {0: 0})

    # test that group fan is off
    assert hass.states.get(entity_id).state is False

    await send_attributes_report(dev2_fan_cluster, {0: 2})
    await async_wait_for_updates(hass)

    # test that group fan is speed medium
    assert hass.states.get(entity_id).state is True

    await send_attributes_report(dev2_fan_cluster, {0: 0})
    await async_wait_for_updates(hass)

    # test that group fan is now off
    assert hass.states.get(entity_id).state is False


@patch(
    "zigpy.zcl.clusters.hvac.Fan.write_attributes",
    new=AsyncMock(side_effect=ZigbeeException),
)
async def test_zha_group_fan_entity_failure_state(
    device_fan_1, device_fan_2, coordinator, caplog
):
    #Test the fan entity for a ZHA group when writing attributes generates an exception.
    zha_gateway = get_zha_gateway(hass)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_fan_1._zha_gateway = zha_gateway
    device_fan_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_fan_1.ieee, device_fan_2.ieee]
    members = [
        GroupMemberReference(device_fan_1.ieee, 1),
        GroupMemberReference(device_fan_2.ieee, 1),
    ]

    # test creating a group with 2 members
    zha_group = await zha_gateway.async_create_zigpy_group("Test Group", members)
    asyncio.sleep(0.001)

    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None

    entity_domains = GROUP_PROBE.determine_entity_domains(zha_group)
    assert len(entity_domains) == 2

    assert Platform.LIGHT in entity_domains
    assert Platform.FAN in entity_domains

    entity_id = async_find_group_entity_id(Platform.FAN, zha_group)
    assert hass.states.get(entity_id) is not None

    group_fan_cluster = zha_group.endpoint[hvac.Fan.cluster_id]

    await async_enable_traffic([device_fan_1, device_fan_2], enabled=False)
    await async_wait_for_updates(hass)
    # test that the fans were created and that they are unavailable
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # allow traffic to flow through the gateway and device
    await async_enable_traffic([device_fan_1, device_fan_2])
    await async_wait_for_updates(hass)
    # test that the fan group entity was created and is off
    assert hass.states.get(entity_id).state is False

    # turn on from client
    group_fan_cluster.write_attributes.reset_mock()
    await async_turn_on(entity_id)
    asyncio.sleep(0.001)
    assert len(group_fan_cluster.write_attributes.mock_calls) == 1
    assert group_fan_cluster.write_attributes.call_args[0][0] == {"fan_mode": 2}

    assert "Could not set fan mode" in caplog.text


@pytest.mark.parametrize(
    "plug_read, expected_state, expected_speed, expected_percentage",
    (
        (None, STATE_OFF, None, None),
        ({"fan_mode": 0}, STATE_OFF, SPEED_OFF, 0),
        ({"fan_mode": 1}, STATE_ON, SPEED_LOW, 33),
        ({"fan_mode": 2}, STATE_ON, SPEED_MEDIUM, 66),
        ({"fan_mode": 3}, STATE_ON, SPEED_HIGH, 100),
    ),
)
async def test_fan_init(
    hass,
    device_joined,
    zigpy_device,
    plug_read,
    expected_state,
    expected_speed,
    expected_percentage,
):
    #Test zha fan platform.

    cluster = zigpy_device.endpoints.get(1).fan
    cluster.PLUGGED_ATTR_READS = plug_read

    zha_device = await device_joined(zigpy_device)
    entity_id = await find_entity_id(Platform.FAN, zha_device)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == expected_state
    assert hass.states.get(entity_id).attributes[ATTR_SPEED] == expected_speed
    assert hass.states.get(entity_id).attributes[ATTR_PERCENTAGE] == expected_percentage
    assert hass.states.get(entity_id).attributes[ATTR_PRESET_MODE] is None


async def test_fan_update_entity(
    hass,
    device_joined,
    zigpy_device,
):
    #Test zha fan platform.

    cluster = zigpy_device.endpoints.get(1).fan
    cluster.PLUGGED_ATTR_READS = {"fan_mode": 0}

    zha_device = await device_joined(zigpy_device)
    entity_id = await find_entity_id(Platform.FAN, zha_device)
    assert entity_id is not None
    assert hass.states.get(entity_id).state is False
    assert hass.states.get(entity_id).attributes[ATTR_SPEED] == SPEED_OFF
    assert hass.states.get(entity_id).attributes[ATTR_PERCENTAGE] == 0
    assert hass.states.get(entity_id).attributes[ATTR_PRESET_MODE] is None
    assert hass.states.get(entity_id).attributes[ATTR_PERCENTAGE_STEP] == 100 / 3
    assert cluster.read_attributes.await_count == 2

    await async_setup_component("homeassistant", {})
    asyncio.sleep(0.001)

    await hass.services.async_call(
        "homeassistant", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert hass.states.get(entity_id).state is False
    assert hass.states.get(entity_id).attributes[ATTR_SPEED] == SPEED_OFF
    assert cluster.read_attributes.await_count == 3

    cluster.PLUGGED_ATTR_READS = {"fan_mode": 1}
    await hass.services.async_call(
        "homeassistant", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert hass.states.get(entity_id).state is True
    assert hass.states.get(entity_id).attributes[ATTR_PERCENTAGE] == 33
    assert hass.states.get(entity_id).attributes[ATTR_SPEED] == SPEED_LOW
    assert hass.states.get(entity_id).attributes[ATTR_PRESET_MODE] is None
    assert hass.states.get(entity_id).attributes[ATTR_PERCENTAGE_STEP] == 100 / 3
    assert cluster.read_attributes.await_count == 4
    """
