"""Switch platform for zhawss."""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, cast

from zigpy.zcl.clusters.general import OnOff
from zigpy.zcl.foundation import Status

from zhaws.server.platforms import BaseEntity, GroupEntity, PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_ON_OFF
from zhaws.server.zigbee.cluster.general import OnOffClusterHandler
from zhaws.server.zigbee.group import Group

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.SWITCH)
GROUP_MATCH = functools.partial(PLATFORM_ENTITIES.group_match, Platform.SWITCH)


class BaseSwitch(BaseEntity):
    """Common base class for zhawss switches."""

    PLATFORM = Platform.SWITCH

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the switch."""
        self._on_off_cluster_handler: OnOffClusterHandler
        self._state: bool | None = None
        super().__init__(*args, **kwargs)

    @property
    def is_on(self) -> bool:
        """Return if the switch is on based on the statemachine."""
        if self._state is None:
            return False
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        result = await self._on_off_cluster_handler.on()
        if not isinstance(result, list) or result[1] is not Status.SUCCESS:
            return
        self._state = True
        self.maybe_send_state_changed_event()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        result = await self._on_off_cluster_handler.off()
        if not isinstance(result, list) or result[1] is not Status.SUCCESS:
            return
        self._state = False
        self.maybe_send_state_changed_event()

    def get_state(self) -> dict:
        """Return the state of the switch."""
        response = super().get_state()
        response["state"] = self.is_on
        return response


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ON_OFF)
class Switch(PlatformEntity, BaseSwitch):
    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the switch."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._on_off_cluster_handler: OnOffClusterHandler = cast(
            OnOffClusterHandler, self.cluster_handlers[CLUSTER_HANDLER_ON_OFF]
        )
        self._state: bool = bool(self._on_off_cluster_handler.on_off)
        self._on_off_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle state update from cluster handler."""
        self._state = bool(event.value)
        self.maybe_send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve on off state from the switch."""
        await super().async_update()
        if self._on_off_cluster_handler:
            state = await self._on_off_cluster_handler.get_attribute_value("on_off")
            if state is not None:
                self._state = state
                self.maybe_send_state_changed_event()


@GROUP_MATCH()
class SwitchGroup(GroupEntity, BaseSwitch):
    """Representation of a switch group."""

    def __init__(self, group: Group):
        """Initialize a switch group."""
        super().__init__(group)
        self._on_off_cluster_handler = group.zigpy_group.endpoint[OnOff.cluster_id]

    def update(self, _: Any | None = None) -> None:
        """Query all members and determine the light group state."""
        self.debug("Updating switch group entity state")
        platform_entities = self._group.get_platform_entities(self.PLATFORM)
        all_entities = [entity.to_json() for entity in platform_entities]
        all_states = [entity["state"] for entity in all_entities]
        self.debug(
            "All platform entity states for group entity members: %s", all_states
        )
        on_states = [state for state in all_states if state["state"]]

        self._state = len(on_states) > 0
        self._available = any(entity.available for entity in platform_entities)

        self.maybe_send_state_changed_event()
