"""Cover platform for zhawss."""
from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Any, Final, Union

from zigpy.zcl.foundation import Status

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_COVER,
    CLUSTER_HANDLER_LEVEL,
    CLUSTER_HANDLER_ON_OFF,
    CLUSTER_HANDLER_SHADE,
)
from zhaws.server.zigbee.cluster.general import LevelChangeEvent

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.COVER)

ATTR_CURRENT_POSITION: Final[str] = "current_position"
ATTR_CURRENT_TILT_POSITION: Final[str] = "current_tilt_position"
ATTR_POSITION: Final[str] = "position"
ATTR_TILT_POSITION: Final[str] = "tilt_position"

STATE_OPEN: Final[str] = "open"
STATE_OPENING: Final[str] = "opening"
STATE_CLOSED: Final[str] = "closed"
STATE_CLOSING: Final[str] = "closing"

_LOGGER = logging.getLogger(__name__)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_COVER)
class Cover(PlatformEntity):
    """Representation of a zhawss cover."""

    PLATFORM = Platform.COVER

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the cover."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cover_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_COVER
        ]
        self._current_position = None
        self._state = None
        if (
            self._cover_cluster_handler
        ):  # TODO this should brobably be changed to raise if None
            self._current_position = 100 - self._cover_cluster_handler.cluster.get(
                "current_position_lift_percentage"
            )
            if self._current_position == 0:
                self._state = STATE_CLOSED
            elif self._current_position == 100:
                self._state = STATE_OPEN
        self._cover_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        if self.current_cover_position is None:
            return None
        return self.current_cover_position == 0

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._state == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._state == STATE_CLOSING

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of ZHA cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_position

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle position update from cluster handler."""
        _LOGGER.debug("setting position: %s", event.value)
        self._current_position = 100 - event.value
        if self._current_position == 0:
            self._state = STATE_CLOSED
        elif self._current_position == 100:
            self._state = STATE_OPEN
        self.maybe_send_state_changed_event()

    def async_update_state(self, state: Any) -> None:
        """Handle state update from cluster handler."""
        _LOGGER.debug("state=%s", state)
        self._state = state
        self.maybe_send_state_changed_event()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the window cover."""
        res = await self._cover_cluster_handler.up_open()
        if isinstance(res, list) and res[1] is Status.SUCCESS:
            self.async_update_state(STATE_OPENING)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the window cover."""
        res = await self._cover_cluster_handler.down_close()
        if isinstance(res, list) and res[1] is Status.SUCCESS:
            self.async_update_state(STATE_CLOSING)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the roller shutter to a specific position."""
        new_pos = kwargs[ATTR_POSITION]
        res = await self._cover_cluster_handler.go_to_lift_percentage(100 - new_pos)
        if isinstance(res, list) and res[1] is Status.SUCCESS:
            self.async_update_state(
                STATE_CLOSING if new_pos < self._current_position else STATE_OPENING
            )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the window cover."""
        res = await self._cover_cluster_handler.stop()
        if isinstance(res, list) and res[1] is Status.SUCCESS:
            self._state = (
                STATE_OPEN
                if self._current_position is not None and self._current_position > 0
                else STATE_CLOSED
            )
            self.maybe_send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve the open/close state of the cover."""
        await super().async_update()
        await self.async_get_state()

    async def async_get_state(self, from_cache: bool = True) -> None:
        """Fetch the current state."""
        _LOGGER.debug("polling current state")
        if self._cover_cluster_handler:
            pos = await self._cover_cluster_handler.get_attribute_value(
                "current_position_lift_percentage", from_cache=from_cache
            )
            _LOGGER.debug("read pos=%s", pos)

            if pos is not None:
                self._current_position = 100 - pos
                self._state = (
                    STATE_OPEN
                    if self.current_cover_position is not None
                    and self.current_cover_position > 0
                    else STATE_CLOSED
                )
            else:
                self._current_position = None
                self._state = None

    def get_state(self) -> dict:
        """Get the state of the cover."""
        response = super().get_state()
        response.update(
            {
                ATTR_CURRENT_POSITION: self.current_cover_position,
                "state": self._state,
                "is_opening": self.is_opening,
                "is_closing": self.is_closing,
                "is_closed": self.is_closed,
            }
        )
        return response


@MULTI_MATCH(
    cluster_handler_names={
        CLUSTER_HANDLER_LEVEL,
        CLUSTER_HANDLER_ON_OFF,
        CLUSTER_HANDLER_SHADE,
    }
)
class Shade(PlatformEntity):
    """ZHAWSS Shade."""

    PLATFORM = Platform.COVER

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the cover."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._on_off_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_ON_OFF
        ]
        self._level_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_LEVEL
        ]
        self._is_open: bool = bool(self._on_off_cluster_handler.on_off)
        position = self._level_cluster_handler.current_level
        position = max(0, min(255, position))
        self._position: Union[int, None] = int(position * 100 / 255)
        self._on_off_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )
        self._level_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._position

    @property
    def is_closed(self) -> Union[bool, None]:
        """Return True if shade is closed."""
        return not self._is_open

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Set open/closed state."""
        self._is_open = bool(event.value)
        self.maybe_send_state_changed_event()

    def handle_cluster_handler_set_level(self, event: LevelChangeEvent) -> None:
        """Set the reported position."""
        value = max(0, min(255, event.level))
        self._position = int(value * 100 / 255)
        self.maybe_send_state_changed_event()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the window cover."""
        res = await self._on_off_cluster_handler.on()
        if not isinstance(res, list) or res[1] != Status.SUCCESS:
            self.debug("couldn't open cover: %s", res)
            return

        self._is_open = True
        self.maybe_send_state_changed_event()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the window cover."""
        res = await self._on_off_cluster_handler.off()
        if not isinstance(res, list) or res[1] != Status.SUCCESS:
            self.debug("couldn't open cover: %s", res)
            return

        self._is_open = False
        self.maybe_send_state_changed_event()

    async def async_set_cover_position(self, position: int, **kwargs: Any) -> None:
        """Move the roller shutter to a specific position."""
        res = await self._level_cluster_handler.move_to_level_with_on_off(
            position * 255 / 100, 1
        )

        if not isinstance(res, list) or res[1] != Status.SUCCESS:
            self.debug("couldn't set cover's position: %s", res)
            return

        self._position = position
        self.maybe_send_state_changed_event()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        res = await self._level_cluster_handler.stop()
        if not isinstance(res, list) or res[1] != Status.SUCCESS:
            self.debug("couldn't stop cover: %s", res)
            return

    def get_state(self) -> dict:
        """Get the state of the cover."""
        response = super().get_state()
        response.update(
            {
                ATTR_CURRENT_POSITION: self._position,
                "is_closed": self.is_closed,
            }
        )
        return response


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_LEVEL, CLUSTER_HANDLER_ON_OFF},
    manufacturers="Keen Home Inc",
)
class KeenVent(Shade):
    """Keen vent cover."""

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        position = self._position or 100
        tasks = [
            self._level_cluster_handler.move_to_level_with_on_off(
                position * 255 / 100, 1
            ),
            self._on_off_cluster_handler.on(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        if any(isinstance(result, Exception) for result in results):
            self.debug("couldn't open cover")
            return

        self._is_open = True
        self._position = position
        self.maybe_send_state_changed_event()
