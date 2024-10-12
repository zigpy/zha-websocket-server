"""Websocket API for zhawss."""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypeVar, Union, cast

from pydantic import Field
from zigpy.profiles import PROFILES
from zigpy.types.named import EUI64

from zha.zigbee.device import Device
from zha.zigbee.group import Group, GroupMemberReference
from zhaws.server.const import DEVICES, DURATION, GROUPS, APICommands
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.websocket.api.model import WebSocketCommand
from zhaws.server.zigbee.controller import Controller

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

GROUP = "group"
MFG_CLUSTER_ID_START = 0xFC00

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


def ensure_list(value: T | None) -> list[T] | list[Any]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return cast("list[T]", value) if isinstance(value, list) else [value]


class StartNetworkCommand(WebSocketCommand):
    """Start the Zigbee network."""

    command: Literal[APICommands.START_NETWORK] = APICommands.START_NETWORK


@decorators.websocket_command(StartNetworkCommand)
@decorators.async_response
async def start_network(
    server: Server, client: Client, command: StartNetworkCommand
) -> None:
    """Start the Zigbee network."""
    await server.controller.start_network()
    client.send_result_success(command)


class StopNetworkCommand(WebSocketCommand):
    """Stop the Zigbee network."""

    command: Literal[APICommands.STOP_NETWORK] = APICommands.STOP_NETWORK


@decorators.websocket_command(StopNetworkCommand)
@decorators.async_response
async def stop_network(
    server: Server, client: Client, command: StopNetworkCommand
) -> None:
    """Stop the Zigbee network."""
    await server.controller.stop_network()
    client.send_result_success(command)


class UpdateTopologyCommand(WebSocketCommand):
    """Stop the Zigbee network."""

    command: Literal[APICommands.UPDATE_NETWORK_TOPOLOGY] = (
        APICommands.UPDATE_NETWORK_TOPOLOGY
    )


@decorators.websocket_command(UpdateTopologyCommand)
@decorators.async_response
async def update_topology(
    server: Server, client: Client, command: WebSocketCommand
) -> None:
    """Update the Zigbee network topology."""
    await server.controller.application_controller.topology.scan()
    client.send_result_success(command)


class GetDevicesCommand(WebSocketCommand):
    """Get all Zigbee devices."""

    command: Literal[APICommands.GET_DEVICES] = APICommands.GET_DEVICES


def zha_device_info(device: Device) -> dict:
    """Get ZHA device information."""
    device_info = {}
    device_info.update(dataclasses.asdict(device.device_info))
    device_info["ieee"] = str(device_info["ieee"])
    device_info["signature"]["node_descriptor"] = device_info["signature"][
        "node_descriptor"
    ].as_dict()
    device_info["entities"] = {
        f"{key[0]}-{key[1]}": dataclasses.asdict(platform_entity.info_object)
        for key, platform_entity in device.platform_entities.items()
    }

    for entity in device_info["entities"].values():
        del entity["cluster_handlers"]

    # Return endpoint device type Names
    names = []
    for endpoint in (ep for epid, ep in device.device.endpoints.items() if epid):
        profile = PROFILES.get(endpoint.profile_id)
        if profile and endpoint.device_type is not None:
            # DeviceType provides undefined enums
            names.append({"name": profile.DeviceType(endpoint.device_type).name})
        else:
            names.append(
                {
                    "name": f"unknown {endpoint.device_type} device_type "
                    f"of 0x{(endpoint.profile_id or 0xFFFF):04x} profile id"
                }
            )
    device_info["endpoint_names"] = names

    return device_info


@decorators.websocket_command(GetDevicesCommand)
@decorators.async_response
async def get_devices(
    server: Server, client: Client, command: GetDevicesCommand
) -> None:
    """Get Zigbee devices."""
    response_devices: dict[str, dict] = {
        str(ieee): zha_device_info(device)
        for ieee, device in server.controller.gateway.devices.items()
    }
    _LOGGER.info("devices: %s", response_devices)
    client.send_result_success(command, {DEVICES: response_devices})


class ReconfigureDeviceCommand(WebSocketCommand):
    """Reconfigure a zigbee device."""

    command: Literal[APICommands.RECONFIGURE_DEVICE] = APICommands.RECONFIGURE_DEVICE
    ieee: EUI64


@decorators.websocket_command(ReconfigureDeviceCommand)
@decorators.async_response
async def reconfigure_device(
    server: Server, client: Client, command: ReconfigureDeviceCommand
) -> None:
    """Reconfigure a zigbee device."""
    device = server.controller.devices.get(command.ieee)
    if device:
        await device.async_configure()
    client.send_result_success(command)


class GetGroupsCommand(WebSocketCommand):
    """Get all Zigbee devices."""

    command: Literal[APICommands.GET_GROUPS] = APICommands.GET_GROUPS


@decorators.websocket_command(GetGroupsCommand)
@decorators.async_response
async def get_groups(server: Server, client: Client, command: GetGroupsCommand) -> None:
    """Get Zigbee groups."""
    groups: dict[int, Any] = {
        id: group.to_json() for id, group in server.controller.groups.items()
    }
    _LOGGER.info("groups: %s", groups)
    client.send_result_success(command, {GROUPS: groups})


class PermitJoiningCommand(WebSocketCommand):
    """Permit joining."""

    command: Literal[APICommands.PERMIT_JOINING] = APICommands.PERMIT_JOINING
    duration: Annotated[int, Field(ge=1, le=254)] = 60
    ieee: Union[EUI64, None] = None


@decorators.websocket_command(PermitJoiningCommand)
@decorators.async_response
async def permit_joining(
    server: Server, client: Client, command: PermitJoiningCommand
) -> None:
    """Permit joining devices to the Zigbee network."""
    # TODO add permit with code support
    await server.controller.application_controller.permit(
        command.duration, command.ieee
    )
    client.send_result_success(
        command,
        {DURATION: command.duration},
    )


class RemoveDeviceCommand(WebSocketCommand):
    """Remove device command."""

    command: Literal[APICommands.REMOVE_DEVICE] = APICommands.REMOVE_DEVICE
    ieee: EUI64


@decorators.websocket_command(RemoveDeviceCommand)
@decorators.async_response
async def remove_device(
    server: Server, client: Client, command: RemoveDeviceCommand
) -> None:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.remove(command.ieee)
    client.send_result_success(command)


class ReadClusterAttributesCommand(WebSocketCommand):
    """Read cluster attributes command."""

    command: Literal[APICommands.READ_CLUSTER_ATTRIBUTES] = (
        APICommands.READ_CLUSTER_ATTRIBUTES
    )
    ieee: EUI64
    endpoint_id: int
    cluster_id: int
    cluster_type: Literal["in", "out"]
    attributes: list[str]
    manufacturer_code: Union[int, None] = None


@decorators.websocket_command(ReadClusterAttributesCommand)
@decorators.async_response
async def read_cluster_attributes(
    server: Server, client: Client, command: ReadClusterAttributesCommand
) -> None:
    """Read the specified cluster attributes."""
    device: Device = server.controller.devices[command.ieee]
    if not device:
        client.send_result_error(
            command,
            "Device not found",
            f"Device with ieee: {command.ieee} not found",
        )
        return
    endpoint_id = command.endpoint_id
    cluster_id = command.cluster_id
    cluster_type = command.cluster_type
    attributes = command.attributes
    manufacturer = command.manufacturer_code
    if cluster_id >= MFG_CLUSTER_ID_START and manufacturer is None:
        manufacturer = device.manufacturer_code
    cluster = device.async_get_cluster(
        endpoint_id, cluster_id, cluster_type=cluster_type
    )
    if not cluster:
        client.send_result_error(
            command,
            "Cluster not found",
            f"Cluster: {endpoint_id}:{command.cluster_id} not found on device with ieee: {str(command.ieee)} not found",
        )
        return
    success, failure = await cluster.read_attributes(
        attributes, allow_cache=False, only_cache=False, manufacturer=manufacturer
    )
    client.send_result_success(
        command,
        {
            "device": {
                "ieee": command.ieee,
            },
            "cluster": {
                "id": cluster.cluster_id,
                "endpoint_id": cluster.endpoint.endpoint_id,
                "name": cluster.name,
                "endpoint_attribute": cluster.ep_attribute,
            },
            "manufacturer_code": manufacturer,
            "succeeded": success,
            "failed": failure,
        },
    )


class WriteClusterAttributeCommand(WebSocketCommand):
    """Write cluster attribute command."""

    command: Literal[APICommands.WRITE_CLUSTER_ATTRIBUTE] = (
        APICommands.WRITE_CLUSTER_ATTRIBUTE
    )
    ieee: EUI64
    endpoint_id: int
    cluster_id: int
    cluster_type: Literal["in", "out"]
    attribute: str
    value: Union[str, int, float, bool]
    manufacturer_code: Union[int, None] = None


@decorators.websocket_command(WriteClusterAttributeCommand)
@decorators.async_response
async def write_cluster_attribute(
    server: Server, client: Client, command: WriteClusterAttributeCommand
) -> None:
    """Set the value of the specific cluster attribute."""
    device: Device = server.controller.devices[command.ieee]
    if not device:
        client.send_result_error(
            command,
            "Device not found",
            f"Device with ieee: {command.ieee} not found",
        )
        return
    endpoint_id = command.endpoint_id
    cluster_id = command.cluster_id
    cluster_type = command.cluster_type
    attribute = command.attribute
    value = command.value
    manufacturer = command.manufacturer_code
    if cluster_id >= MFG_CLUSTER_ID_START and manufacturer is None:
        manufacturer = device.manufacturer_code
    cluster = device.async_get_cluster(
        endpoint_id, cluster_id, cluster_type=cluster_type
    )
    if not cluster:
        client.send_result_error(
            command,
            "Cluster not found",
            f"Cluster: {endpoint_id}:{command.cluster_id} not found on device with ieee: {str(command.ieee)} not found",
        )
        return
    response = await device.write_zigbee_attribute(
        endpoint_id,
        cluster_id,
        attribute,
        value,
        cluster_type=cluster_type,
        manufacturer=manufacturer,
    )
    client.send_result_success(
        command,
        {
            "device": {
                "ieee": str(command.ieee),
            },
            "cluster": {
                "id": cluster.cluster_id,
                "endpoint_id": cluster.endpoint.endpoint_id,
                "name": cluster.name,
                "endpoint_attribute": cluster.ep_attribute,
            },
            "manufacturer_code": manufacturer,
            "response": {
                "attribute": attribute,
                "status": response[0][0].status.name,
            },  # TODO there has to be a better way to do this
        },
    )


class CreateGroupCommand(WebSocketCommand):
    """Create group command."""

    command: Literal[APICommands.CREATE_GROUP] = APICommands.CREATE_GROUP
    group_name: str
    members: list[GroupMemberReference]
    group_id: Union[int, None] = None


@decorators.websocket_command(CreateGroupCommand)
@decorators.async_response
async def create_group(
    server: Server, client: Client, command: CreateGroupCommand
) -> None:
    """Create a new group."""
    controller: Controller = server.controller
    group_name = command.group_name
    members = command.members
    group_id = command.group_id
    group: Group = await controller.async_create_zigpy_group(
        group_name, members, group_id
    )
    client.send_result_success(command, {"group": group.to_json()})


class RemoveGroupsCommand(WebSocketCommand):
    """Remove groups command."""

    command: Literal[APICommands.REMOVE_GROUPS] = APICommands.REMOVE_GROUPS
    group_ids: list[int]


@decorators.websocket_command(RemoveGroupsCommand)
@decorators.async_response
async def remove_groups(
    server: Server, client: Client, command: RemoveGroupsCommand
) -> None:
    """Remove the specified groups."""
    controller: Controller = server.controller
    group_ids = command.group_ids

    if len(group_ids) > 1:
        tasks = []
        for group_id in group_ids:
            tasks.append(controller.async_remove_zigpy_group(group_id))
        await asyncio.gather(*tasks)
    else:
        await controller.async_remove_zigpy_group(group_ids[0])
    groups: dict[int, Any] = {
        id: group.to_json() for id, group in server.controller.groups.items()
    }
    client.send_result_success(command, {GROUPS: groups})


class AddGroupMembersCommand(WebSocketCommand):
    """Add group members command."""

    command: Literal[
        APICommands.ADD_GROUP_MEMBERS, APICommands.REMOVE_GROUP_MEMBERS
    ] = APICommands.ADD_GROUP_MEMBERS
    group_id: int
    members: list[GroupMemberReference]


@decorators.websocket_command(AddGroupMembersCommand)
@decorators.async_response
async def add_group_members(
    server: Server, client: Client, command: AddGroupMembersCommand
) -> None:
    """Add members to a ZHA group."""
    controller: Controller = server.controller
    group_id = command.group_id
    members = command.members
    group = None

    if group_id in controller.groups:
        group = controller.groups[group_id]
        await group.async_add_members(members)
    if not group:
        client.send_result_error(command, "G1", "ZHA Group not found")
        return
    ret_group = group.to_json()
    client.send_result_success(command, {GROUP: ret_group})


class RemoveGroupMembersCommand(AddGroupMembersCommand):
    """Remove group members command."""

    command: Literal[APICommands.REMOVE_GROUP_MEMBERS] = (
        APICommands.REMOVE_GROUP_MEMBERS
    )


@decorators.websocket_command(RemoveGroupMembersCommand)
@decorators.async_response
async def remove_group_members(
    server: Server, client: Client, command: RemoveGroupMembersCommand
) -> None:
    """Remove members from a ZHA group."""
    controller: Controller = server.controller
    group_id = command.group_id
    members = command.members
    group = None

    if group_id in controller.groups:
        group = controller.groups[group_id]
        await group.async_remove_members(members)
    if not group:
        client.send_result_error(command, "G1", "ZHA Group not found")
        return
    ret_group = group.to_json()
    client.send_result_success(command, {GROUP: ret_group})


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, start_network)
    register_api_command(server, stop_network)
    register_api_command(server, get_devices)
    register_api_command(server, reconfigure_device)
    register_api_command(server, get_groups)
    register_api_command(server, create_group)
    register_api_command(server, remove_groups)
    register_api_command(server, add_group_members)
    register_api_command(server, remove_group_members)
    register_api_command(server, permit_joining)
    register_api_command(server, remove_device)
    register_api_command(server, update_topology)
    register_api_command(server, read_cluster_attributes)
    register_api_command(server, write_cluster_attribute)
