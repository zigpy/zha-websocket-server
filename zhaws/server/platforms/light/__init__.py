"""Light platform for zhawss."""
from __future__ import annotations

import asyncio
import enum
import functools
from typing import TYPE_CHECKING, Any, Final, Optional, Union

from zigpy.zcl.foundation import Status

from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.platforms.util import color as color_util
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_COLOR,
    CLUSTER_HANDLER_IDENTIFY,
    CLUSTER_HANDLER_LEVEL,
    CLUSTER_HANDLER_ON_OFF,
)

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.LIGHT)

CAPABILITIES_COLOR_LOOP = 0x4
CAPABILITIES_COLOR_XY = 0x08
CAPABILITIES_COLOR_TEMP = 0x10

DEFAULT_TRANSITION = 1

UPDATE_COLORLOOP_ACTION = 0x1
UPDATE_COLORLOOP_DIRECTION = 0x2
UPDATE_COLORLOOP_TIME = 0x4
UPDATE_COLORLOOP_HUE = 0x8

UNSUPPORTED_ATTRIBUTE = 0x86

# Float that represents transition time in seconds to make change.
ATTR_TRANSITION: Final[str] = "transition"

# Lists holding color values
ATTR_RGB_COLOR: Final[str] = "rgb_color"
ATTR_RGBW_COLOR: Final[str] = "rgbw_color"
ATTR_RGBWW_COLOR: Final[str] = "rgbww_color"
ATTR_XY_COLOR: Final[str] = "xy_color"
ATTR_HS_COLOR: Final[str] = "hs_color"
ATTR_COLOR_TEMP: Final[str] = "color_temp"
ATTR_KELVIN: Final[str] = "kelvin"
ATTR_MIN_MIREDS: Final[str] = "min_mireds"
ATTR_MAX_MIREDS: Final[str] = "max_mireds"
ATTR_COLOR_NAME: Final[str] = "color_name"
ATTR_WHITE_VALUE: Final[str] = "white_value"
ATTR_WHITE: Final[str] = "white"

# Brightness of the light, 0..255 or percentage
ATTR_BRIGHTNESS: Final[str] = "brightness"
ATTR_BRIGHTNESS_PCT: Final[str] = "brightness_pct"
ATTR_BRIGHTNESS_STEP: Final[str] = "brightness_step"
ATTR_BRIGHTNESS_STEP_PCT: Final[str] = "brightness_step_pct"

# String representing a profile (built-in ones or external defined).
ATTR_PROFILE: Final[str] = "profile"

# If the light should flash, can be FLASH_SHORT or FLASH_LONG.
ATTR_FLASH: Final[str] = "flash"
FLASH_SHORT: Final[str] = "short"
FLASH_LONG: Final[str] = "long"

# List of possible effects
ATTR_EFFECT_LIST: Final[str] = "effect_list"

# Apply an effect to the light, can be EFFECT_COLORLOOP.
ATTR_EFFECT: Final[str] = "effect"
EFFECT_COLORLOOP: Final[str] = "colorloop"
EFFECT_RANDOM: Final[str] = "random"
EFFECT_WHITE: Final[str] = "white"

# Bitfield of features supported by the light entity
SUPPORT_BRIGHTNESS: Final[int] = 1  # Deprecated, replaced by color modes
SUPPORT_COLOR_TEMP: Final[int] = 2  # Deprecated, replaced by color modes
SUPPORT_EFFECT: Final[int] = 4
SUPPORT_FLASH: Final[int] = 8
SUPPORT_COLOR: Final[int] = 16  # Deprecated, replaced by color modes
SUPPORT_TRANSITION: Final[int] = 32
SUPPORT_WHITE_VALUE: Final[int] = 128  # Deprecated, replaced by color modes

EFFECT_BLINK: Final[int] = 0x00
EFFECT_BREATHE: Final[int] = 0x01
EFFECT_OKAY: Final[int] = 0x02
EFFECT_DEFAULT_VARIANT: Final[int] = 0x00

FLASH_EFFECTS: Final[dict[str, int]] = {
    FLASH_SHORT: EFFECT_BLINK,
    FLASH_LONG: EFFECT_BREATHE,
}


class LightColorMode(enum.IntEnum):
    """ZCL light color mode enum."""

    HS_COLOR = 0x00
    XY_COLOR = 0x01
    COLOR_TEMP = 0x02


class BaseLight(PlatformEntity):
    """Operations common to all light entities."""

    PLATFORM = Platform.LIGHT
    _FORCE_ON = False

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the light."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._available: bool = False
        self._brightness: Union[int, None] = None
        self._off_brightness: Union[int, None] = None
        self._hs_color: Union[tuple[float, float], None] = None
        self._color_temp: Union[int, None] = None
        self._min_mireds: Union[int, None] = 153
        self._max_mireds: Union[int, None] = 500
        self._effect_list: Union[list[str], None] = None
        self._effect: Union[str, None] = None
        self._supported_features: int = 0
        self._state: bool | None = None
        self._on_off_cluster_handler: ClusterHandler
        self._level_cluster_handler: Optional[ClusterHandler] = None
        self._color_cluster_handler: Optional[ClusterHandler] = None
        self._identify_cluster_handler: Optional[ClusterHandler] = None
        self._default_transition: int | None = None

    def get_state(self) -> dict[str, Any]:
        """Return the state of the light."""
        state: dict[str, Any] = {}
        state["on"] = self.is_on
        state["brightness"] = self.brightness
        state["hs_color"] = self.hs_color
        state["color_temp"] = self.color_temp
        state["effect"] = self.effect
        state["off_brightness"] = self._off_brightness
        return state

    @property
    def is_on(self) -> bool:
        """Return true if entity is on."""
        if self._state is None:
            return False
        return self._state

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light."""
        return self._brightness

    @property
    def min_mireds(self) -> int | None:
        """Return the coldest color_temp that this light supports."""
        return self._min_mireds

    @property
    def max_mireds(self) -> int | None:
        """Return the warmest color_temp that this light supports."""
        return self._max_mireds

    def cluster_handler_set_level(self, value: int) -> None:
        """Set the brightness of this light between 0..254.
        brightness level 255 is a special value instructing the device to come
        on at `on_level` Zigbee attribute value, regardless of the last set
        level
        """
        value = max(0, min(254, value))
        self._brightness = value
        self.send_state_changed_event()

    @property
    def hs_color(self) -> Optional[tuple[float, float]]:
        """Return the hs color value [int, int]."""
        return self._hs_color

    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self._color_temp

    @property
    def effect_list(self) -> list[str] | None:
        """Return the list of supported effects."""
        return self._effect_list

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._effect

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    def to_json(self) -> dict:
        """Return a JSON representation of the select."""
        json = super().to_json()
        json["supported_features"] = self.supported_features
        json["effect_list"] = self.effect_list
        json["min_mireds"] = self.min_mireds
        json["max_mireds"] = self.max_mireds
        return json

    async def async_turn_on(self, transition=None, **kwargs: Any) -> None:
        """Turn the entity on."""
        duration = (
            transition * 10
            if transition
            else self._default_transition * 10
            if self._default_transition
            else DEFAULT_TRANSITION
        )
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        effect = kwargs.get(ATTR_EFFECT)
        flash = kwargs.get(ATTR_FLASH)

        if brightness is None and self._off_brightness is not None:
            brightness = self._off_brightness

        t_log = {}
        if (
            brightness is not None or transition
        ) and self._supported_features & SUPPORT_BRIGHTNESS:
            if brightness is not None:
                level = min(254, brightness)
            else:
                level = self._brightness or 254
            result = await self._level_cluster_handler.move_to_level_with_on_off(
                level, duration
            )
            t_log["move_to_level_with_on_off"] = result
            if not isinstance(result, list) or result[1] is not Status.SUCCESS:
                self.debug("turned on: %s", t_log)
                return
            self._state = bool(level)
            if level:
                self._brightness = level

        if brightness is None or (self._FORCE_ON and brightness):
            # since some lights don't always turn on with move_to_level_with_on_off,
            # we should call the on command on the on_off cluster if brightness is not 0.
            result = await self._on_off_cluster_handler.on()
            t_log["on_off"] = result
            if not isinstance(result, list) or result[1] is not Status.SUCCESS:
                self.debug("turned on: %s", t_log)
                return
            self._state = True
        if ATTR_COLOR_TEMP in kwargs and self.supported_features & SUPPORT_COLOR_TEMP:
            temperature = kwargs[ATTR_COLOR_TEMP]
            result = await self._color_cluster_handler.move_to_color_temp(
                temperature, duration
            )
            t_log["move_to_color_temp"] = result
            if not isinstance(result, list) or result[1] is not Status.SUCCESS:
                self.debug("turned on: %s", t_log)
                return
            self._color_temp = temperature
            self._hs_color = None

        if ATTR_HS_COLOR in kwargs and self.supported_features & SUPPORT_COLOR:
            hs_color = kwargs[ATTR_HS_COLOR]
            xy_color = color_util.color_hs_to_xy(*hs_color)
            result = await self._color_cluster_handler.move_to_color(
                int(xy_color[0] * 65535), int(xy_color[1] * 65535), duration
            )
            t_log["move_to_color"] = result
            if not isinstance(result, list) or result[1] is not Status.SUCCESS:
                self.debug("turned on: %s", t_log)
                return
            self._hs_color = hs_color
            self._color_temp = None

        if effect == EFFECT_COLORLOOP and self.supported_features & SUPPORT_EFFECT:
            result = await self._color_cluster_handler.color_loop_set(
                UPDATE_COLORLOOP_ACTION
                | UPDATE_COLORLOOP_DIRECTION
                | UPDATE_COLORLOOP_TIME,
                0x2,  # start from current hue
                0x1,  # only support up
                transition if transition else 7,  # transition
                0,  # no hue
            )
            t_log["color_loop_set"] = result
            self._effect = EFFECT_COLORLOOP
        elif (
            self._effect == EFFECT_COLORLOOP
            and effect != EFFECT_COLORLOOP
            and self.supported_features & SUPPORT_EFFECT
        ):
            result = await self._color_cluster_handler.color_loop_set(
                UPDATE_COLORLOOP_ACTION,
                0x0,
                0x0,
                0x0,
                0x0,  # update action only, action off, no dir, time, hue
            )
            t_log["color_loop_set"] = result
            self._effect = None

        if flash is not None and self._supported_features & SUPPORT_FLASH:
            result = await self._identify_cluster_handler.trigger_effect(
                FLASH_EFFECTS[flash], EFFECT_DEFAULT_VARIANT
            )
            t_log["trigger_effect"] = result

        self._off_brightness = None
        self.debug("turned on: %s", t_log)
        self.send_state_changed_event()

    async def async_turn_off(self, transition=None, **kwargs):
        """Turn the entity off."""
        duration = transition
        supports_level = self.supported_features & SUPPORT_BRIGHTNESS

        if duration and supports_level:
            result = await self._level_cluster_handler.move_to_level_with_on_off(
                0, duration * 10
            )
        else:
            result = await self._on_off_cluster_handler.off()
        self.debug("turned off: %s", result)
        if not isinstance(result, list) or result[1] is not Status.SUCCESS:
            return
        self._state = False

        if duration and supports_level:
            # store current brightness so that the next turn_on uses it.
            self._off_brightness = self._brightness

        self.send_state_changed_event()


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
)
class Light(BaseLight):
    """Representation of a light for zhawss."""

    _REFRESH_INTERVAL = (2700, 4500)

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the light."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._on_off_cluster_handler = self.cluster_handlers[CLUSTER_HANDLER_ON_OFF]
        self._state = bool(self._on_off_cluster_handler.on_off)
        self._level_cluster_handler = self.cluster_handlers.get(CLUSTER_HANDLER_LEVEL)
        self._color_cluster_handler = self.cluster_handlers.get(CLUSTER_HANDLER_COLOR)
        self._identify_cluster_handler = self.cluster_handlers.get(
            CLUSTER_HANDLER_IDENTIFY
        )
        if self._color_cluster_handler:
            self._min_mireds: Union[int, None] = self._color_cluster_handler.min_mireds
            self._max_mireds: Union[int, None] = self._color_cluster_handler.max_mireds
        self._cancel_refresh_handle = None
        effect_list = []

        if self._level_cluster_handler:
            self._supported_features |= SUPPORT_BRIGHTNESS
            self._supported_features |= SUPPORT_TRANSITION
            self._brightness = self._level_cluster_handler.current_level

        if self._color_cluster_handler:
            color_capabilities = self._color_cluster_handler.color_capabilities
            if color_capabilities & CAPABILITIES_COLOR_TEMP:
                self._supported_features |= SUPPORT_COLOR_TEMP
                self._color_temp = self._color_cluster_handler.color_temperature

            if color_capabilities & CAPABILITIES_COLOR_XY:
                self._supported_features |= SUPPORT_COLOR
                curr_x = self._color_cluster_handler.current_x
                curr_y = self._color_cluster_handler.current_y
                if curr_x is not None and curr_y is not None:
                    self._hs_color = color_util.color_xy_to_hs(
                        float(curr_x / 65535), float(curr_y / 65535)
                    )
                else:
                    self._hs_color = (0, 0)

            if color_capabilities & CAPABILITIES_COLOR_LOOP:
                self._supported_features |= SUPPORT_EFFECT
                effect_list.append(EFFECT_COLORLOOP)
                if self._color_cluster_handler.color_loop_active == 1:
                    self._effect = EFFECT_COLORLOOP

        if self._identify_cluster_handler:
            self._supported_features |= SUPPORT_FLASH

        if effect_list:
            self._effect_list = effect_list

        """TODO
        self._default_transition = async_get_zha_config_value(
            zha_device.gateway.config_entry,
            ZHA_OPTIONS,
            CONF_DEFAULT_LIGHT_TRANSITION,
            0,
        )
        """

        self._on_off_cluster_handler.add_listener(self)
        self._level_cluster_handler.add_listener(self)

        @periodic(self._REFRESH_INTERVAL)
        async def _refresh() -> None:
            """Call async_get_state at an interval."""
            await self.async_update()
            self.send_state_changed_event()

        self._cancel_refresh_handle = asyncio.create_task(_refresh())

        """TODO
        self.async_accept_signal(
            None,
            SIGNAL_LIGHT_GROUP_STATE_CHANGED,
            self._maybe_force_refresh,
            signal_override=True,
        )
        """

    def cluster_handler_attribute_updated(
        self, attr_id: int, attr_name: str, value: Any
    ) -> None:
        """Set the state."""
        self._state = bool(value)
        if value:
            self._off_brightness = None
        self.send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve the state from the light."""
        if not self.available:
            return
        self.debug("polling current state")
        if self._on_off_cluster_handler:
            state = await self._on_off_cluster_handler.get_attribute_value(
                "on_off", from_cache=False
            )
            if state is not None:
                self._state = state
        if self._level_cluster_handler:
            level = await self._level_cluster_handler.get_attribute_value(
                "current_level", from_cache=False
            )
            if level is not None:
                self._brightness = level
        if self._color_cluster_handler:
            attributes = [
                "color_mode",
                "color_temperature",
                "current_x",
                "current_y",
                "color_loop_active",
            ]

            results = await self._color_cluster_handler.get_attributes(
                attributes, from_cache=False
            )

            if (color_mode := results.get("color_mode")) is not None:
                if color_mode == LightColorMode.COLOR_TEMP:
                    color_temp = results.get("color_temperature")
                    if color_temp is not None and color_mode:
                        self._color_temp = color_temp
                        self._hs_color = None
                else:
                    color_x = results.get("current_x")
                    color_y = results.get("current_y")
                    if color_x is not None and color_y is not None:
                        self._hs_color = color_util.color_xy_to_hs(
                            float(color_x / 65535), float(color_y / 65535)
                        )
                        self._color_temp = None

            color_loop_active = results.get("color_loop_active")
            if color_loop_active is not None:
                if color_loop_active == 1:
                    self._effect = EFFECT_COLORLOOP
                else:
                    self._effect = None

    """TODO
    async def _maybe_force_refresh(self, signal):
        #Force update the state if the signal contains the entity id for this entity.
        if self.entity_id in signal["entity_ids"]:
            await self.async_get_state()
            self.send_state_changed_event()
    """


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
    manufacturers={"Philips", "Signify Netherlands B.V."},
)
class HueLight(Light):
    """Representation of a HUE light which does not report attributes."""

    _REFRESH_INTERVAL = (180, 300)


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
    manufacturers={"Jasco", "Quotra-Vision"},
)
class ForceOnLight(Light):
    """Representation of a light which does not respect move_to_level_with_on_off."""

    _FORCE_ON = True
