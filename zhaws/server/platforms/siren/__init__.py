"""Siren platform for zhawss."""
from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING, Any, Final, Union

import zigpy.types as t
from zigpy.zcl.clusters.security import IasWd as WD

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_IAS_WD

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SIREN)
DEFAULT_DURATION: Final[int] = 5  # seconds
WARNING_DEVICE_MODE_STOP: Final[int] = 0
WARNING_DEVICE_MODE_BURGLAR: Final[int] = 1
WARNING_DEVICE_MODE_FIRE: Final[int] = 2
WARNING_DEVICE_MODE_EMERGENCY: Final[int] = 3
WARNING_DEVICE_MODE_POLICE_PANIC: Final[int] = 4
WARNING_DEVICE_MODE_FIRE_PANIC: Final[int] = 5
WARNING_DEVICE_MODE_EMERGENCY_PANIC: Final[int] = 6

WARNING_DEVICE_STROBE_NO: Final[int] = 0
WARNING_DEVICE_STROBE_YES: Final[int] = 1

WARNING_DEVICE_SOUND_LOW: Final[int] = 0
WARNING_DEVICE_SOUND_MEDIUM: Final[int] = 1
WARNING_DEVICE_SOUND_HIGH: Final[int] = 2
WARNING_DEVICE_SOUND_VERY_HIGH: Final[int] = 3

WARNING_DEVICE_STROBE_LOW: Final[int] = 0x00
WARNING_DEVICE_STROBE_MEDIUM: Final[int] = 0x01
WARNING_DEVICE_STROBE_HIGH: Final[int] = 0x02
WARNING_DEVICE_STROBE_VERY_HIGH: Final[int] = 0x03

WARNING_DEVICE_SQUAWK_MODE_ARMED: Final[int] = 0
WARNING_DEVICE_SQUAWK_MODE_DISARMED: Final[int] = 1

ATTR_TONE: Final[str] = "tone"

ATTR_AVAILABLE_TONES: Final[str] = "available_tones"
ATTR_DURATION: Final[str] = "duration"
ATTR_VOLUME_LEVEL: Final[str] = "volume_level"

SUPPORT_TURN_ON: Final[int] = 1
SUPPORT_TURN_OFF: Final[int] = 2
SUPPORT_TONES: Final[int] = 4
SUPPORT_VOLUME_SET: Final[int] = 8
SUPPORT_DURATION: Final[int] = 16


class Strobe(t.enum8):  # type: ignore #TODO fix type
    """Strobe enum."""

    No_Strobe = 0x00
    Strobe = 0x01


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class Siren(PlatformEntity):
    """Representation of a zhawss siren."""

    PLATFORM = Platform.SIREN

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the siren."""
        self._attr_supported_features = (
            SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_DURATION
            | SUPPORT_VOLUME_SET
            | SUPPORT_TONES
        )
        self._attr_available_tones: Union[
            list[Union[int, str]], dict[int, str], None
        ] = {
            WARNING_DEVICE_MODE_BURGLAR: "Burglar",
            WARNING_DEVICE_MODE_FIRE: "Fire",
            WARNING_DEVICE_MODE_EMERGENCY: "Emergency",
            WARNING_DEVICE_MODE_POLICE_PANIC: "Police Panic",
            WARNING_DEVICE_MODE_FIRE_PANIC: "Fire Panic",
            WARNING_DEVICE_MODE_EMERGENCY_PANIC: "Emergency Panic",
        }
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandler = cluster_handlers[0]
        self._attr_is_on: bool = False
        self._off_listener: asyncio.TimerHandle | None = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on siren."""
        if self._off_listener:
            self._off_listener.cancel()
            self._off_listener = None
        tone_cache = self._cluster_handler.data_cache.get(
            WD.Warning.WarningMode.__name__
        )
        siren_tone = (
            tone_cache.value
            if tone_cache is not None
            else WARNING_DEVICE_MODE_EMERGENCY
        )
        siren_duration = DEFAULT_DURATION
        level_cache = self._cluster_handler.data_cache.get(
            WD.Warning.SirenLevel.__name__
        )
        siren_level = (
            level_cache.value if level_cache is not None else WARNING_DEVICE_SOUND_HIGH
        )
        strobe_cache = self._cluster_handler.data_cache.get(Strobe.__name__)
        should_strobe = (
            strobe_cache.value if strobe_cache is not None else Strobe.No_Strobe
        )
        strobe_level_cache = self._cluster_handler.data_cache.get(
            WD.StrobeLevel.__name__
        )
        strobe_level = (
            strobe_level_cache.value
            if strobe_level_cache is not None
            else WARNING_DEVICE_STROBE_HIGH
        )
        if (duration := kwargs.get(ATTR_DURATION)) is not None:
            siren_duration = duration
        if (tone := kwargs.get(ATTR_TONE)) is not None:
            siren_tone = tone
        if (level := kwargs.get(ATTR_VOLUME_LEVEL)) is not None:
            siren_level = int(level)
        await self._cluster_handler.issue_start_warning(
            mode=siren_tone,
            warning_duration=siren_duration,
            siren_level=siren_level,
            strobe=should_strobe,
            strobe_duty_cycle=50 if should_strobe else 0,
            strobe_intensity=strobe_level,
        )
        self._attr_is_on = True
        self._off_listener = asyncio.get_running_loop().call_later(
            siren_duration, self.async_set_off
        )
        self.maybe_send_state_changed_event()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off siren."""
        await self._cluster_handler.issue_start_warning(
            mode=WARNING_DEVICE_MODE_STOP, strobe=WARNING_DEVICE_STROBE_NO
        )
        self._attr_is_on = False
        self.maybe_send_state_changed_event()

    def async_set_off(self) -> None:
        """Set is_on to False and write HA state."""
        self._attr_is_on = False
        if self._off_listener:
            self._off_listener.cancel()
            self._off_listener = None
        self.maybe_send_state_changed_event()

    def to_json(self) -> dict:
        json = super().to_json()
        json[ATTR_AVAILABLE_TONES] = self._attr_available_tones
        json["supported_features"] = self._attr_supported_features
        return json

    def get_state(self) -> dict:
        """Get the state of the siren."""
        response = super().get_state()
        response["state"] = self._attr_is_on
        return response
