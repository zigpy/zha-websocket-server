"""Group for zhaws."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import zigpy.exceptions

from zhaws.server.platforms import PlatformEntity
from zhaws.server.util import LogMixin

if TYPE_CHECKING:
    from zigpy.group import Endpoint as ZigpyEndpoint, Group as ZigpyGroup

    from zhaws.server.platforms import GroupEntity
    from zhaws.server.websocket.server import Server
    from zhaws.server.zigbee.device import Device

_LOGGER = logging.getLogger(__name__)


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
    def member_info(self) -> dict[str, Any]:
        """Get group info."""  # TODO do we need this information
        member_info: dict[str, Any] = {}
        member_info["endpoint_id"] = self.endpoint_id
        member_info["device"] = self.device.zha_device_info
        member_info["entities"] = self.associated_entities
        return member_info

    @property
    def associated_entities(self) -> list[PlatformEntity]:
        """Return the list of entities that were derived from this endpoint."""
        return [
            platform_entity
            for platform_entity in self._device.platform_entities.values()
            if platform_entity.endpoint.id == self.endpoint_id
        ]

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

    def log(self, level: int, msg: str, *args: Any) -> None:
        """Log a message."""
        msg = f"[%s](%s): {msg}"
        args = (f"0x{self._group.group_id:04x}", self.endpoint_id) + args
        _LOGGER.log(level, msg, *args)


class Group:
    """Representation of a Zigbee group."""

    def __init__(self, group: ZigpyGroup, server: Server) -> None:
        """Initialize the group."""
        self._group: ZigpyGroup = group
        self._server: Server = server
        self._members: dict[str, Device] = {}
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
    def members(self) -> dict[str, Device]:
        """Return the members of the group."""
        return self._members

    @property
    def platform_entities(self) -> dict[str, GroupEntity]:
        """Return the platform entities of the group."""
        return self._platform_entities

    """
    @property
    def members(self) -> list[ZHAGroupMember]:
        #Return the ZHA devices that are members of this group.
        return [
            ZHAGroupMember(
                self, self._zha_gateway.devices.get(member_ieee), endpoint_id
            )
            for (member_ieee, endpoint_id) in self._zigpy_group.members.keys()
            if member_ieee in self._zha_gateway.devices
        ]

    async def async_add_members(self, members: list[GroupMember]) -> None:
        #Add members to this group.
        if len(members) > 1:
            tasks = []
            for member in members:
                tasks.append(
                    self._zha_gateway.devices[member.ieee].async_add_endpoint_to_group(
                        member.endpoint_id, self.group_id
                    )
                )
            await asyncio.gather(*tasks)
        else:
            await self._zha_gateway.devices[
                members[0].ieee
            ].async_add_endpoint_to_group(members[0].endpoint_id, self.group_id)

    async def async_remove_members(self, members: list[GroupMember]) -> None:
        #Remove members from this group.
        if len(members) > 1:
            tasks = []
            for member in members:
                tasks.append(
                    self._zha_gateway.devices[
                        member.ieee
                    ].async_remove_endpoint_from_group(
                        member.endpoint_id, self.group_id
                    )
                )
            await asyncio.gather(*tasks)
        else:
            await self._zha_gateway.devices[
                members[0].ieee
            ].async_remove_endpoint_from_group(members[0].endpoint_id, self.group_id)

    @property
    def member_entity_ids(self) -> list[str]:
        #Return the ZHA entity ids for all entities for the members of this group.
        all_entity_ids: list[str] = []
        for member in self.members:
            entity_references = member.associated_entities
            for entity_reference in entity_references:
                all_entity_ids.append(entity_reference["entity_id"])
        return all_entity_ids

    def get_domain_entity_ids(self, domain) -> list[str]:
        #Return entity ids from the entity domain for this group.
        domain_entity_ids: list[str] = []
        for member in self.members:
            if member.device.is_coordinator:
                continue
            entities = async_entries_for_device(
                self._zha_gateway.ha_entity_registry,
                member.device.device_id,
                include_disabled_entities=True,
            )
            domain_entity_ids.extend(
                [entity.entity_id for entity in entities if entity.domain == domain]
            )
        return domain_entity_ids

    @property
    def group_info(self) -> dict[str, Any]:
        #Get ZHA group info.
        group_info: dict[str, Any] = {}
        group_info["group_id"] = self.group_id
        group_info["name"] = self.name
        group_info["members"] = [member.member_info for member in self.members]
        return group_info

    def log(self, level: int, msg: str, *args):
        #Log a message.
        msg = f"[%s](%s): {msg}"
        args = (self.name, self.group_id) + args
        _LOGGER.log(level, msg, *args)
"""
