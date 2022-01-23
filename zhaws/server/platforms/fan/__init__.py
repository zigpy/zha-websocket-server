"""Fan platform for zhawss."""
from __future__ import annotations

from abc import abstractmethod
import functools
import math
from typing import TYPE_CHECKING, Any, Final, Union

from zigpy.exceptions import ZigbeeException
from zigpy.zcl.clusters import hvac

from zhaws.server.platforms import BaseEntity, GroupEntity, PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_FAN
from zhaws.server.zigbee.group import Group

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.FAN)
GROUP_MATCH = functools.partial(PLATFORM_ENTITIES.group_match, Platform.FAN)

# Additional speeds in zigbee's ZCL
# Spec is unclear as to what this value means. On King Of Fans HBUniversal
# receiver, this means Very High.
PRESET_MODE_ON: Final[str] = "on"
# The fan speed is self-regulated
PRESET_MODE_AUTO: Final[str] = "auto"
# When the heated/cooled space is occupied, the fan is always on
PRESET_MODE_SMART: Final[str] = "smart"

SPEED_RANGE: Final = (1, 3)  # off is not included
PRESET_MODES_TO_NAME: Final[dict[int, str]] = {
    4: PRESET_MODE_ON,
    5: PRESET_MODE_AUTO,
    6: PRESET_MODE_SMART,
}

NAME_TO_PRESET_MODE = {v: k for k, v in PRESET_MODES_TO_NAME.items()}
PRESET_MODES = list(NAME_TO_PRESET_MODE)

DEFAULT_ON_PERCENTAGE: Final[int] = 50

ATTR_PERCENTAGE: Final[str] = "percentage"
ATTR_PRESET_MODE: Final[str] = "preset_mode"
SUPPORT_SET_SPEED: Final[int] = 1


def ranged_value_to_percentage(
    low_high_range: tuple[float, float], value: float
) -> int:
    """Given a range of low and high values convert a single value to a percentage.
    When using this utility for fan speeds, do not include 0 if it is off
    Given a low value of 1 and a high value of 255 this function
    will return:
    (1,255), 255: 100
    (1,255), 127: 50
    (1,255), 10: 4
    """
    offset = low_high_range[0] - 1
    return int(((value - offset) * 100) // states_in_range(low_high_range))


def percentage_to_ranged_value(
    low_high_range: tuple[float, float], percentage: int
) -> float:
    """Given a range of low and high values convert a percentage to a single value.
    When using this utility for fan speeds, do not include 0 if it is off
    Given a low value of 1 and a high value of 255 this function
    will return:
    (1,255), 100: 255
    (1,255), 50: 127.5
    (1,255), 4: 10.2
    """
    offset = low_high_range[0] - 1
    return states_in_range(low_high_range) * percentage / 100 + offset


def states_in_range(low_high_range: tuple[float, float]) -> float:
    """Given a range of low and high values return how many states exist."""
    return low_high_range[1] - low_high_range[0] + 1


def int_states_in_range(low_high_range: tuple[float, float]) -> int:
    """Given a range of low and high values return how many integer states exist."""
    return int(states_in_range(low_high_range))


class NotValidPresetModeError(ValueError):
    """Exception class when the preset_mode in not in the preset_modes list."""


class BaseFan(BaseEntity):
    """Base representation of a zhawss fan."""

    PLATFORM = Platform.FAN

    @property
    def preset_modes(self) -> list[str]:
        """Return the available preset modes."""
        return PRESET_MODES

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    async def async_turn_on(
        self,
        speed: str | None = None,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        if percentage is None:
            percentage = DEFAULT_ON_PERCENTAGE
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.async_set_percentage(0)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percenage of the fan."""
        fan_mode = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self._async_set_fan_mode(fan_mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for the fan."""
        if preset_mode not in self.preset_modes:
            raise NotValidPresetModeError(
                f"The preset_mode {preset_mode} is not a valid preset_mode: {self.preset_modes}"
            )
        await self._async_set_fan_mode(NAME_TO_PRESET_MODE[preset_mode])

    @abstractmethod
    async def _async_set_fan_mode(self, fan_mode: int) -> None:
        """Set the fan mode for the fan."""

    def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle state update from cluster handler."""
        self.maybe_send_state_changed_event()

    def to_json(self) -> dict:
        """Return a JSON representation of the binary sensor."""
        json = super().to_json()
        json["preset_modes"] = self.preset_modes
        json["supported_features"] = self.supported_features
        json["speed_count"] = self.speed_count
        return json


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_FAN)
class Fan(PlatformEntity, BaseFan):
    """Representation of a zhawss fan."""

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the fan."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._fan_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_FAN
        ]
        self._fan_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def percentage(self) -> Union[int, None]:
        """Return the current speed percentage."""
        if (
            self._fan_cluster_handler.fan_mode is None
            or self._fan_cluster_handler.fan_mode > SPEED_RANGE[1]
        ):
            return None
        if self._fan_cluster_handler.fan_mode == 0:
            return 0
        return ranged_value_to_percentage(
            SPEED_RANGE, self._fan_cluster_handler.fan_mode
        )

    @property
    def preset_mode(self) -> Union[str, None]:
        """Return the current preset mode."""
        return PRESET_MODES_TO_NAME.get(self._fan_cluster_handler.fan_mode)

    def async_set_state(self, attr_id: int, attr_name: str, value: Any) -> None:
        """Handle state update from cluster handler."""
        self.maybe_send_state_changed_event()

    async def _async_set_fan_mode(self, fan_mode: int) -> None:
        """Set the fan mode for the fan."""
        await self._fan_cluster_handler.async_set_speed(fan_mode)
        self.async_set_state(0, "fan_mode", fan_mode)

    def get_state(self) -> dict:
        """Return the state of the fan."""
        response = super().get_state()
        response.update(
            {
                "preset_mode": self.preset_mode,
                "percentage": self.percentage,
            }
        )
        return response


@GROUP_MATCH()
class FanGroup(GroupEntity, BaseFan):
    """Representation of a fan group."""

    def __init__(self, group: Group):
        """Initialize a fan group."""
        super().__init__(group)
        self._fan_channel = group.zigpy_group.endpoint[hvac.Fan.cluster_id]
        self._percentage = None
        self._preset_mode = None

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return self._percentage

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        return self._preset_mode

    def get_state(self) -> dict:
        """Return the state of the fan."""
        response = super().get_state()
        response.update(
            {
                "preset_mode": self.preset_mode,
                "percentage": self.percentage,
            }
        )
        return response

    async def _async_set_fan_mode(self, fan_mode: int) -> None:
        """Set the fan mode for the group."""
        try:
            await self._fan_channel.write_attributes({"fan_mode": fan_mode})
        except ZigbeeException as ex:
            self.error("Could not set fan mode: %s", ex)
        self.update()

    def update(self, _: Any = None) -> None:
        """Attempt to retrieve on off state from the fan."""
        self.debug("Updating fan group entity state")
        platform_entities = self._group.get_platform_entities(self.PLATFORM)
        all_entities = [entity.to_json() for entity in platform_entities]
        all_states = [entity["state"] for entity in all_entities]
        self.debug(
            "All platform entity states for group entity members: %s", all_states
        )

        self._available = any(entity.available for entity in platform_entities)
        percentage_states: list[dict] = [
            state for state in all_states if state.get(ATTR_PERCENTAGE)
        ]
        preset_mode_states: list[dict] = [
            state for state in all_states if state.get(ATTR_PRESET_MODE)
        ]

        if percentage_states:
            self._percentage = percentage_states[0][ATTR_PERCENTAGE]
            self._preset_mode = None
        elif preset_mode_states:
            self._preset_mode = preset_mode_states[0][ATTR_PRESET_MODE]
            self._percentage = None
        else:
            self._percentage = None
            self._preset_mode = None

        self.maybe_send_state_changed_event()
