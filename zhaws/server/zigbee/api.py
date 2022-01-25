"""Websocket API for zhawss."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Mapping, TypeVar, cast

import voluptuous as vol
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.types.named import EUI64

from zhaws.server.const import (
    COMMAND,
    CONF_BAUDRATE,
    CONF_DATABASE,
    CONF_ENABLE_QUIRKS,
    CONF_FLOWCONTROL,
    CONF_RADIO_TYPE,
    DEVICES,
    DURATION,
    GROUPS,
    IEEE,
    APICommands,
)
from zhaws.server.websocket.api import decorators, register_api_command
from zhaws.server.zigbee.controller import Controller
from zhaws.server.zigbee.device import (
    ATTR_ATTRIBUTE,
    ATTR_CLUSTER_ID,
    ATTR_CLUSTER_TYPE,
    ATTR_ENDPOINT_ID,
    ATTR_MANUFACTURER_CODE,
    ATTR_VALUE,
    Device,
)
from zhaws.server.zigbee.group import Group, GroupMemberReference

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

GROUP = "group"
GROUP_ID = "group_id"
GROUP_IDS = "group_ids"
GROUP_NAME = "group_name"
ATTR_MEMBERS = "members"
MFG_CLUSTER_ID_START = 0xFC00

_LOGGER = logging.getLogger(__name__)

positive_int = vol.All(vol.Coerce(int), vol.Range(min=0))

T = TypeVar("T")


def ensure_list(value: T | None) -> list[T] | list[Any]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return cast("list[T]", value) if isinstance(value, list) else [value]


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.START_NETWORK),
        vol.Required(CONF_RADIO_TYPE): str,
        vol.Required(CONF_DEVICE): vol.Schema(
            {
                vol.Required(CONF_DEVICE_PATH): str,
                vol.Optional(CONF_FLOWCONTROL): str,
                vol.Required(CONF_BAUDRATE): decorators.POSITIVE_INT,
            }
        ),
        vol.Required(CONF_DATABASE): str,
        vol.Required(CONF_ENABLE_QUIRKS): bool,
    }
)
@decorators.async_response
async def start_network(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Start the Zigbee network."""
    await server.controller.start_network(message)
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.STOP_NETWORK),
    }
)
@decorators.async_response
async def stop_network(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Stop the Zigbee network."""
    await server.controller.stop_network()
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.UPDATE_NETWORK_TOPOLOGY),
    }
)
@decorators.async_response
async def update_topology(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Update the Zigbee network topology."""
    await server.controller.application_controller.topology.scan()
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.GET_DEVICES),
    }
)
@decorators.async_response
async def get_devices(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Get Zigbee devices."""
    response_devices: dict[str, dict] = {
        str(ieee): device.zha_device_info
        for ieee, device in server.controller.devices.items()
    }
    _LOGGER.info("devices: %s", response_devices)
    client.send_result_success(message, {DEVICES: response_devices})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.RECONFIGURE_DEVICE),
        vol.Required(IEEE): EUI64.convert,
    }
)
@decorators.async_response
async def reconfigure_device(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Reconfigure a zigbee device."""
    device = server.controller.devices.get(message[IEEE])
    if device:
        await device.async_configure()
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.GET_GROUPS),
    }
)
@decorators.async_response
async def get_groups(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Get Zigbee groups."""
    groups: dict[int, Any] = {
        id: group.to_json() for id, group in server.controller.groups.items()
    }
    _LOGGER.info("groups: %s", groups)
    client.send_result_success(message, {GROUPS: groups})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.PERMIT_JOINING),
        vol.Optional(DURATION, default=60): vol.All(vol.Coerce(int), vol.Range(0, 254)),
        vol.Optional(IEEE, default=None): EUI64.convert,
    }
)
@decorators.async_response
async def permit_joining(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    # TODO add permit with code support
    await server.controller.application_controller.permit(
        message[DURATION], message[IEEE]
    )
    client.send_result_success(
        message,
        {DURATION: message[DURATION]},
    )


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.REMOVE_DEVICE),
        vol.Required(IEEE): str,
    }
)
@decorators.async_response
async def remove_device(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Permit joining devices to the Zigbee network."""
    await server.controller.application_controller.remove(
        EUI64.convert(message["ieee"])
    )
    client.send_result_success(message)


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.READ_CLUSTER_ATTRIBUTES),
        vol.Required(IEEE): EUI64.convert,
        vol.Required(ATTR_ENDPOINT_ID): int,
        vol.Required(ATTR_CLUSTER_ID): int,
        vol.Required(ATTR_CLUSTER_TYPE): str,
        vol.Required("attributes"): vol.All(ensure_list, [str]),
        vol.Optional(ATTR_MANUFACTURER_CODE): int,
    }
)
@decorators.async_response
async def read_cluster_attributes(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Read the specified cluster attributes."""
    device: Device = server.controller.devices[message[IEEE]]
    if not device:
        client.send_result_error(
            message,
            "Device not found",
            f"Device with ieee: {message[IEEE]} not found",
        )
        return
    endpoint_id = message[ATTR_ENDPOINT_ID]
    cluster_id = message[ATTR_CLUSTER_ID]
    cluster_type = message[ATTR_CLUSTER_TYPE]
    attributes = message["attributes"]
    manufacturer = message.get(ATTR_MANUFACTURER_CODE)
    if cluster_id >= MFG_CLUSTER_ID_START and manufacturer is None:
        manufacturer = device.manufacturer_code
    cluster = device.async_get_cluster(
        endpoint_id, cluster_id, cluster_type=cluster_type
    )
    if not cluster:
        client.send_result_error(
            message,
            "Cluster not found",
            f"Cluster: {endpoint_id}:{message[ATTR_CLUSTER_ID]} not found on device with ieee: {message[IEEE]} not found",
        )
        return
    success, failure = await cluster.read_attributes(
        attributes, allow_cache=False, only_cache=False, manufacturer=manufacturer
    )
    client.send_result_success(
        message,
        {
            "device": {
                "ieee": str(message[IEEE]),
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


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.WRITE_CLUSTER_ATTRIBUTE),
        vol.Required(IEEE): EUI64.convert,
        vol.Required(ATTR_ENDPOINT_ID): int,
        vol.Required(ATTR_CLUSTER_ID): int,
        vol.Required(ATTR_CLUSTER_TYPE): str,
        vol.Required(ATTR_ATTRIBUTE): str,
        vol.Required(ATTR_VALUE): vol.Any(str, int, float, bool),
        vol.Optional(ATTR_MANUFACTURER_CODE): int,
    }
)
@decorators.async_response
async def write_cluster_attribute(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the value of the specifiec cluster attribute."""
    device: Device = server.controller.devices[message[IEEE]]
    if not device:
        client.send_result_error(
            message,
            "Device not found",
            f"Device with ieee: {message[IEEE]} not found",
        )
        return
    endpoint_id = message[ATTR_ENDPOINT_ID]
    cluster_id = message[ATTR_CLUSTER_ID]
    cluster_type = message[ATTR_CLUSTER_TYPE]
    attribute = message[ATTR_ATTRIBUTE]
    value = message[ATTR_VALUE]
    manufacturer = message.get(ATTR_MANUFACTURER_CODE)
    if cluster_id >= MFG_CLUSTER_ID_START and manufacturer is None:
        manufacturer = device.manufacturer_code
    cluster = device.async_get_cluster(
        endpoint_id, cluster_id, cluster_type=cluster_type
    )
    if not cluster:
        client.send_result_error(
            message,
            "Cluster not found",
            f"Cluster: {endpoint_id}:{message[ATTR_CLUSTER_ID]} not found on device with ieee: {message[IEEE]} not found",
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
        message,
        {
            "device": {
                "ieee": str(message[IEEE]),
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
                "status": response[0][0].status.name,  # type: ignore
            },  # TODO there has to be a better way to do this
        },
    )


def cv_group_member(value: Any) -> GroupMemberReference:
    """Validate and transform a group member."""
    if not isinstance(value, Mapping):
        raise vol.Invalid("Not a group member")
    try:
        group_member = GroupMemberReference(
            ieee=EUI64.convert(value["ieee"]), endpoint_id=value["endpoint_id"]
        )
    except KeyError as err:
        raise vol.Invalid("Not a group member") from err

    return group_member


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.CREATE_GROUP),
        vol.Required(GROUP_NAME): str,
        vol.Optional(GROUP_ID): positive_int,
        vol.Optional(ATTR_MEMBERS): vol.All(ensure_list, [cv_group_member]),
    }
)
@decorators.async_response
async def create_group(server: Server, client: Client, message: dict[str, Any]) -> None:
    """create a new group."""
    controller: Controller = server.controller
    group_name = message[GROUP_NAME]
    members = cast(list[GroupMemberReference], message.get(ATTR_MEMBERS))
    group_id = message.get(GROUP_ID)
    group: Group = await controller.async_create_zigpy_group(
        group_name, members, group_id
    )
    client.send_result_success(message, {"group": group.to_json()})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.REMOVE_GROUPS),
        vol.Required(GROUP_IDS): vol.All(ensure_list, [positive_int]),
    }
)
@decorators.async_response
async def remove_groups(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Remove the specified groups."""
    controller: Controller = server.controller
    group_ids = message[GROUP_IDS]

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
    client.send_result_success(message, {GROUPS: groups})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.ADD_GROUP_MEMBERS),
        vol.Required(GROUP_ID): positive_int,
        vol.Required(ATTR_MEMBERS): vol.All(ensure_list, [cv_group_member]),
    }
)
@decorators.async_response
async def add_group_members(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Add members to a ZHA group."""
    controller: Controller = server.controller
    group_id = message[GROUP_ID]
    members = cast(list[GroupMemberReference], message.get(ATTR_MEMBERS))
    group = None

    if group_id in controller.groups:
        group = controller.groups[group_id]
        await group.async_add_members(members)
    if not group:
        client.send_result_error(message, "G1", "ZHA Group not found")
        return
    ret_group = group.to_json()
    client.send_result_success(message, {GROUP: ret_group})


@decorators.websocket_command(
    {
        vol.Required(COMMAND): str(APICommands.REMOVE_GROUP_MEMBERS),
        vol.Required(GROUP_ID): positive_int,
        vol.Required(ATTR_MEMBERS): vol.All(ensure_list, [cv_group_member]),
    }
)
@decorators.async_response
async def remove_group_members(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Remove members from a ZHA group."""
    controller: Controller = server.controller
    group_id = message[GROUP_ID]
    members = cast(list[GroupMemberReference], message.get(ATTR_MEMBERS))
    group = None

    if group_id in controller.groups:
        group = controller.groups[group_id]
        await group.async_remove_members(members)
    if not group:
        client.send_result_error(message, "G1", "ZHA Group not found")
        return
    ret_group = group.to_json()
    client.send_result_success(message, {GROUP: ret_group})


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, start_network)
    register_api_command(server, stop_network)
    register_api_command(server, get_devices)
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
