"""Lock platform for zhawss."""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Final

from zigpy.zcl.foundation import Status

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_DOORLOCK

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.LOCK)

STATE_LOCKED: Final[str] = "locked"
STATE_UNLOCKED: Final[str] = "unlocked"
STATE_LOCKING: Final[str] = "locking"
STATE_UNLOCKING: Final[str] = "unlocking"
STATE_JAMMED: Final[str] = "jammed"
# The first state is Zigbee 'Not fully locked'
STATE_LIST: Final[list[str]] = [STATE_UNLOCKED, STATE_LOCKED, STATE_UNLOCKED]
VALUE_TO_STATE: Final = dict(enumerate(STATE_LIST))


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_DOORLOCK)
class Lock(PlatformEntity):
    """Representation of a zhawss lock."""

    PLATFORM = Platform.LOCK

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the lock."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._doorlock_cluster_handler: ClusterHandler = cluster_handlers[0]
        self._state = VALUE_TO_STATE.get(
            self._doorlock_cluster_handler.cluster.get("lock_state"), None
        )
        self._doorlock_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def is_locked(self) -> bool:
        """Return true if entity is locked."""
        if self._state is None:
            return False
        return self._state == STATE_LOCKED

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        result = await self._doorlock_cluster_handler.lock_door()
        if not isinstance(result, list) or result[0] is not Status.SUCCESS:
            self.error("Error with lock_door: %s", result)
            return
        self.maybe_send_state_changed_event()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        result = await self._doorlock_cluster_handler.unlock_door()
        if not isinstance(result, list) or result[0] is not Status.SUCCESS:
            self.error("Error with unlock_door: %s", result)
            return
        self.maybe_send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve state from the lock."""
        await super().async_update()
        await self.async_get_state()

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle state update from cluster handler."""
        self._state = VALUE_TO_STATE.get(event.value, self._state)
        self.maybe_send_state_changed_event()

    async def async_get_state(self, from_cache: bool = True) -> None:
        """Attempt to retrieve state from the lock."""
        if self._doorlock_cluster_handler:
            state = await self._doorlock_cluster_handler.get_attribute_value(
                "lock_state", from_cache=from_cache
            )
            if state is not None:
                self._state = VALUE_TO_STATE.get(state, self._state)

    async def async_set_lock_user_code(self, code_slot: int, user_code: str) -> None:
        """Set the user_code to index X on the lock."""
        if self._doorlock_cluster_handler:
            await self._doorlock_cluster_handler.async_set_user_code(
                code_slot, user_code
            )
            self.debug("User code at slot %s set", code_slot)

    async def async_enable_lock_user_code(self, code_slot: int) -> None:
        """Enable user_code at index X on the lock."""
        if self._doorlock_cluster_handler:
            await self._doorlock_cluster_handler.async_enable_user_code(code_slot)
            self.debug("User code at slot %s enabled", code_slot)

    async def async_disable_lock_user_code(self, code_slot: int) -> None:
        """Disable user_code at index X on the lock."""
        if self._doorlock_cluster_handler:
            await self._doorlock_cluster_handler.async_disable_user_code(code_slot)
            self.debug("User code at slot %s disabled", code_slot)

    async def async_clear_lock_user_code(self, code_slot: int) -> None:
        """Clear the user_code at index X on the lock."""
        if self._doorlock_cluster_handler:
            await self._doorlock_cluster_handler.async_clear_user_code(code_slot)
            self.debug("User code at slot %s cleared", code_slot)

    def get_state(self) -> dict:
        """Get the state of the lock."""
        response = super().get_state()
        response["is_locked"] = self.is_locked
        return response
