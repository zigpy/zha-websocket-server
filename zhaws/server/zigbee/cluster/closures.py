"""Closures cluster handlers module for zhawss."""
from typing import Any, Awaitable

from zigpy.zcl.clusters import closures

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClientClusterHandler,
    ClusterAttributeUpdatedEvent,
    ClusterHandler,
)
from zhaws.server.zigbee.cluster.const import REPORT_CONFIG_IMMEDIATE


@registries.CLUSTER_HANDLER_REGISTRY.register(closures.DoorLock.cluster_id)
class DoorLockClusterHandler(ClusterHandler):
    """Door lock cluster handler."""

    _value_attribute = 0
    REPORT_CONFIG = [{"attr": "lock_state", "config": REPORT_CONFIG_IMMEDIATE}]

    async def async_update(self) -> None:
        """Retrieve latest state."""
        result = await self.get_attribute_value("lock_state", from_cache=True)
        if result is not None:
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=0,
                    name="lock_state",
                    value=result,
                ),
            )

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle a cluster command received on this cluster."""

        if (
            self._cluster.client_commands is None
            or self._cluster.client_commands.get(command_id) is None
        ):
            return

        command_name = self._cluster.client_commands.get(command_id, [command_id])[0]
        if command_name == "operation_event_notification":
            self.zha_send_event(
                command_name,
                {
                    "source": args[0].name,
                    "operation": args[1].name,
                    "code_slot": (args[2] + 1),  # start code slots at 1
                },
            )

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute update from lock cluster."""
        attr_name = self.cluster.attributes.get(attrid, [attrid])[0]
        self.debug(
            "Attribute report '%s'[%s] = %s", self.cluster.name, attr_name, value
        )
        if attrid == self._value_attribute:
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=attrid,
                    name=attr_name,
                    value=value,
                ),
            )

    async def async_set_user_code(self, code_slot: int, user_code: str) -> None:
        """Set the user code for the code slot."""

        await self.set_pin_code(
            code_slot - 1,  # start code slots at 1, Zigbee internals use 0
            closures.DoorLock.UserStatus.Enabled,
            closures.DoorLock.UserType.Unrestricted,
            user_code,
        )

    async def async_enable_user_code(self, code_slot: int) -> None:
        """Enable the code slot."""

        await self.set_user_status(code_slot - 1, closures.DoorLock.UserStatus.Enabled)

    async def async_disable_user_code(self, code_slot: int) -> None:
        """Disable the code slot."""

        await self.set_user_status(code_slot - 1, closures.DoorLock.UserStatus.Disabled)

    async def async_get_user_code(self, code_slot: int) -> Awaitable[int]:
        """Get the user code from the code slot."""

        result = await self.get_pin_code(code_slot - 1)
        return result

    async def async_clear_user_code(self, code_slot: int) -> None:
        """Clear the code slot."""

        await self.clear_pin_code(code_slot - 1)

    async def async_clear_all_user_codes(self) -> None:
        """Clear all code slots."""

        await self.clear_all_pin_codes()

    async def async_set_user_type(self, code_slot: int, user_type: str) -> None:
        """Set user type."""

        await self.set_user_type(code_slot - 1, user_type)

    async def async_get_user_type(self, code_slot: int) -> Awaitable[str]:
        """Get user type."""

        result = await self.get_user_type(code_slot - 1)
        return result


@registries.CLUSTER_HANDLER_REGISTRY.register(closures.Shade.cluster_id)
class Shade(ClusterHandler):
    """Shade cluster handler."""


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(closures.WindowCovering.cluster_id)
class WindowCoveringClient(ClientClusterHandler):
    """Window client cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(closures.WindowCovering.cluster_id)
class WindowCovering(ClusterHandler):
    """Window cluster handler."""

    _value_attribute = 8
    REPORT_CONFIG = [
        {"attr": "current_position_lift_percentage", "config": REPORT_CONFIG_IMMEDIATE},
    ]

    async def async_update(self) -> None:
        """Retrieve latest state."""
        result = await self.get_attribute_value(
            "current_position_lift_percentage", from_cache=False
        )
        self.debug("read current position: %s", result)
        if result is not None:
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=8,
                    name="current_position_lift_percentage",
                    value=result,
                ),
            )

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute update from window_covering cluster."""
        attr_name = self.cluster.attributes.get(attrid, [attrid])[0]
        self.debug(
            "Attribute report '%s'[%s] = %s", self.cluster.name, attr_name, value
        )
        if attrid == self._value_attribute:
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=attrid,
                    name=attr_name,
                    value=value,
                ),
            )
