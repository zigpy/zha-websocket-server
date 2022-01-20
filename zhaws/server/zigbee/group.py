"""Group for zhaws."""
from __future__ import annotations

import asyncio
import collections
import logging
from typing import TYPE_CHECKING, Any

import zigpy.exceptions

from zhaws.server.platforms import PlatformEntity
from zhaws.server.util import LogMixin

if TYPE_CHECKING:
    from zigpy.group import Endpoint as ZigpyEndpoint, Group as ZigpyGroup
    from zigpy.types.named import EUI64

    from zhaws.server.platforms import GroupEntity
    from zhaws.server.websocket.server import Server
    from zhaws.server.zigbee.device import Device

_LOGGER = logging.getLogger(__name__)


GroupMemberReference = collections.namedtuple(
    "GroupMemberReference", "ieee endpoint_id"
)


class GroupMember(LogMixin):
    """Composite object that represents a device endpoint in a Zigbee group."""

    def __init__(self, group: Group, device: Device, endpoint_id: int) -> None:
        """Initialize the group member."""
        self._group: Group = group
        self._device: Device = device
        self._endpoint_id: int = endpoint_id

    @property
    def group(self) -> Group:
        """Return the group this member belongs to."""
        return self._group

    @property
    def endpoint_id(self) -> int:
        """Return the endpoint id for this group member."""
        return self._endpoint_id

    @property
    def endpoint(self) -> ZigpyEndpoint:
        """Return the endpoint for this group member."""
        return self._device.device.endpoints.get(self.endpoint_id)

    @property
    def device(self) -> Device:
        """Return the zha device for this group member."""
        return self._device

    @property
    def associated_entities(self) -> list[PlatformEntity]:
        """Return the list of entities that were derived from this endpoint."""
        return [
            platform_entity
            for platform_entity in self._device.platform_entities.values()
            if platform_entity.endpoint.id == self.endpoint_id
        ]

    def to_json(self) -> dict[str, Any]:
        """Get group info."""
        member_info: dict[str, Any] = {}
        member_info["endpoint_id"] = self.endpoint_id
        member_info["device"] = self.device.zha_device_info
        member_info["entities"] = {
            entity.unique_id: entity.to_json() for entity in self.associated_entities
        }
        return member_info

    async def async_remove_from_group(self) -> None:
        """Remove the device endpoint from the provided zigbee group."""
        try:
            await self._device.device.endpoints[self._endpoint_id].remove_from_group(
                self._group.group_id
            )
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to remove endpoint: %s for device '%s' from group: 0x%04x ex: %s",
                self._endpoint_id,
                self._device.ieee,
                self._group.group_id,
                str(ex),
            )

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message."""
        msg = f"[%s](%s): {msg}"
        args = (f"0x{self._group.group_id:04x}", self.endpoint_id) + args
        _LOGGER.log(level, msg, *args, **kwargs)


class Group(LogMixin):
    """Representation of a Zigbee group."""

    def __init__(self, group: ZigpyGroup, server: Server) -> None:
        """Initialize the group."""
        self._group: ZigpyGroup = group
        self._server: Server = server
        self._platform_entities: dict[str, GroupEntity] = {}

    @property
    def group_id(self) -> int:
        """Return the group id."""
        return self._group.group_id

    @property
    def name(self) -> str:
        """Return the name of the group."""
        return self._group.name

    @property
    def platform_entities(self) -> dict[str, GroupEntity]:
        """Return the platform entities of the group."""
        return self._platform_entities

    @property
    def zigpy_group(self) -> ZigpyGroup:
        """Return the zigpy group."""
        return self._group

    @property
    def members(self) -> list[GroupMember]:
        """Return the ZHA devices that are members of this group."""
        devices: dict[EUI64, Device] = self._server.controller.devices
        return [
            GroupMember(self, devices[member_ieee], endpoint_id)
            for (member_ieee, endpoint_id) in self._group.members.keys()
            if member_ieee in devices
        ]

    async def async_add_members(self, members: list[GroupMemberReference]) -> None:
        """Add members to this group."""
        devices: dict[str, Device] = self._server.controller.get_devices()
        if len(members) > 1:
            tasks = []
            for member in members:
                tasks.append(
                    devices[member.ieee].async_add_endpoint_to_group(
                        member.endpoint_id, self.group_id
                    )
                )
            await asyncio.gather(*tasks)
        else:
            member = members[0]
            await devices[member.ieee].async_add_endpoint_to_group(
                member.endpoint_id, self.group_id
            )

    async def async_remove_members(self, members: list[GroupMemberReference]) -> None:
        """Remove members from this group."""
        devices: dict[str, Device] = self._server.controller.get_devices()
        if len(members) > 1:
            tasks = []
            for member in members:
                tasks.append(
                    devices[member.ieee].async_remove_endpoint_from_group(
                        member.endpoint_id, self.group_id
                    )
                )
            await asyncio.gather(*tasks)
        else:
            member = members[0]
            await devices[member.ieee].async_remove_endpoint_from_group(
                member.endpoint_id, self.group_id
            )

    @property
    def member_entity_ids(self) -> list[PlatformEntity]:
        """Return the platform entities for the members of this group."""
        all_entities: list[PlatformEntity] = []
        for member in self.members:
            entities = member.associated_entities
            for entity in entities:
                all_entities.append(entity)
        return all_entities

    def get_platform_entities(self, platform: str) -> list[PlatformEntity]:
        """Return entities belonging to the specified platform for this group."""
        platform_entities: list[PlatformEntity] = []
        for member in self.members:
            if member.device.is_coordinator:
                continue
            for entity in member.associated_entities:
                if entity.PLATFORM == platform:
                    platform_entities.append(entity)

        return platform_entities

    def to_json(self) -> dict[str, Any]:
        """Get ZHA group info."""
        group_info: dict[str, Any] = {}
        group_info["id"] = self.group_id
        group_info["name"] = self.name
        group_info["members"] = {
            str(member.device.ieee): member.to_json() for member in self.members
        }
        group_info["entities"] = {
            unique_id: entity.to_json()
            for unique_id, entity in self._platform_entities.items()
        }
        return group_info

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message."""
        msg = f"[%s](%s): {msg}"
        args = (self.name, self.group_id) + args
        _LOGGER.log(level, msg, *args, **kwargs)
