"""Climate platform for zhawss."""
from __future__ import annotations

import asyncio
from datetime import datetime
import functools
import logging
from typing import TYPE_CHECKING, Any, Final, Optional, Union

from zigpy.zcl.clusters.hvac import Fan as FanCluster, Thermostat as ThermostatCluster

from zhaws.backports.enum import StrEnum
from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterAttributeUpdatedEvent,
)
from zhaws.server.zigbee.cluster.const import (
    CLUSTER_HANDLER_FAN,
    CLUSTER_HANDLER_THERMOSTAT,
)

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.CLIMATE)
MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.CLIMATE)


ATTR_SYS_MODE: Final[str] = "system_mode"
ATTR_FAN_MODE: Final[str] = "fan_mode"
ATTR_RUNNING_MODE: Final[str] = "running_mode"
ATTR_SETPT_CHANGE_SRC: Final[str] = "setpoint_change_source"
ATTR_SETPT_CHANGE_AMT: Final[str] = "setpoint_change_amount"
ATTR_OCCUPANCY: Final[str] = "occupancy"
ATTR_PI_COOLING_DEMAND: Final[str] = "pi_cooling_demand"
ATTR_PI_HEATING_DEMAND: Final[str] = "pi_heating_demand"
ATTR_OCCP_COOL_SETPT: Final[str] = "occupied_cooling_setpoint"
ATTR_OCCP_HEAT_SETPT: Final[str] = "occupied_heating_setpoint"
ATTR_UNOCCP_HEAT_SETPT: Final[str] = "unoccupied_heating_setpoint"
ATTR_UNOCCP_COOL_SETPT: Final[str] = "unoccupied_cooling_setpoint"
ATTR_HVAC_MODE: Final[str] = "hvac_mode"
ATTR_TARGET_TEMP_HIGH: Final[str] = "target_temp_high"
ATTR_TARGET_TEMP_LOW: Final[str] = "target_temp_low"

SUPPORT_TARGET_TEMPERATURE: Final[int] = 1
SUPPORT_TARGET_TEMPERATURE_RANGE: Final[int] = 2
SUPPORT_TARGET_HUMIDITY: Final[int] = 4
SUPPORT_FAN_MODE: Final[int] = 8
SUPPORT_PRESET_MODE: Final[int] = 16
SUPPORT_SWING_MODE: Final[int] = 32
SUPPORT_AUX_HEAT: Final[int] = 64

PRECISION_TENTHS: Final[float] = 0.1
# Temperature attribute
ATTR_TEMPERATURE: Final[str] = "temperature"
TEMP_CELSIUS: Final[str] = "°C"


class HVACMode(StrEnum):
    OFF = "off"
    # Heating
    HEAT = "heat"
    # Cooling
    COOL = "cool"
    # The device supports heating/cooling to a range
    HEAT_COOL = "heat_cool"
    # The temperature is set based on a schedule, learned behavior, AI or some
    # other related mechanism. User is not able to adjust the temperature
    AUTO = "auto"
    # Device is in Dry/Humidity mode
    DRY = "dry"
    # Only the fan is on, not fan and another mode like cool
    FAN_ONLY = "fan_only"


class Preset(StrEnum):
    # No preset is active
    NONE = "none"
    # Device is running an energy-saving mode
    ECO = "eco"
    # Device is in away mode
    AWAY = "away"
    # Device turn all valve full up
    BOOST = "boost"
    # Device is in comfort mode
    COMFORT = "comfort"
    # Device is in home mode
    HOME = "home"
    # Device is prepared for sleep
    SLEEP = "sleep"
    # Device is reacting to activity (e.g. movement sensors)
    ACTIVITY = "activity"
    SCHEDULE = "Schedule"
    COMPLEX = "Complex"
    TEMP_MANUAL = "Temporary manual"


class FanState(StrEnum):
    # Possible fan state
    ON = "on"
    OFF = "off"
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TOP = "top"
    MIDDLE = "middle"
    FOCUS = "focus"
    DIFFUSE = "diffuse"


class CurrentHVAC(StrEnum):
    OFF = "off"
    HEAT = "heating"
    COOL = "cooling"
    DRY = "drying"
    IDLE = "idle"
    FAN = "fan"


RUNNING_MODE = {0x00: HVACMode.OFF, 0x03: HVACMode.COOL, 0x04: HVACMode.HEAT}

SEQ_OF_OPERATION = {
    0x00: (HVACMode.OFF, HVACMode.COOL),  # cooling only
    0x01: (HVACMode.OFF, HVACMode.COOL),  # cooling with reheat
    0x02: (HVACMode.OFF, HVACMode.HEAT),  # heating only
    0x03: (HVACMode.OFF, HVACMode.HEAT),  # heating with reheat
    # cooling and heating 4-pipes
    0x04: (HVACMode.OFF, HVACMode.HEAT_COOL, HVACMode.COOL, HVACMode.HEAT),
    # cooling and heating 4-pipes
    0x05: (HVACMode.OFF, HVACMode.HEAT_COOL, HVACMode.COOL, HVACMode.HEAT),
    0x06: (HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF),  # centralite specific
    0x07: (HVACMode.HEAT_COOL, HVACMode.OFF),  # centralite specific
}

HVAC_MODE_2_SYSTEM = {
    HVACMode.OFF: ThermostatCluster.SystemMode.Off,
    HVACMode.HEAT_COOL: ThermostatCluster.SystemMode.Auto,
    HVACMode.COOL: ThermostatCluster.SystemMode.Cool,
    HVACMode.HEAT: ThermostatCluster.SystemMode.Heat,
    HVACMode.FAN_ONLY: ThermostatCluster.SystemMode.Fan_only,
    HVACMode.DRY: ThermostatCluster.SystemMode.Dry,
}

SYSTEM_MODE_2_HVAC = {
    ThermostatCluster.SystemMode.Off: HVACMode.OFF,
    ThermostatCluster.SystemMode.Auto: HVACMode.HEAT_COOL,
    ThermostatCluster.SystemMode.Cool: HVACMode.COOL,
    ThermostatCluster.SystemMode.Heat: HVACMode.HEAT,
    ThermostatCluster.SystemMode.Emergency_Heating: HVACMode.HEAT,
    ThermostatCluster.SystemMode.Pre_cooling: HVACMode.COOL,  # this is 'precooling'. is it the same?
    ThermostatCluster.SystemMode.Fan_only: HVACMode.FAN_ONLY,
    ThermostatCluster.SystemMode.Dry: HVACMode.DRY,
    ThermostatCluster.SystemMode.Sleep: HVACMode.OFF,
}

ZCL_TEMP: Final[int] = 100
_LOGGER = logging.getLogger(__name__)


"""TODO implement to_json and get_state methods"""


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class Thermostat(PlatformEntity):

    PLATFORM = Platform.CLIMATE
    DEFAULT_MAX_TEMP = 35
    DEFAULT_MIN_TEMP = 7

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the thermostat."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        if CLUSTER_HANDLER_THERMOSTAT not in self.cluster_handlers:
            raise ValueError("No Thermostat cluster handler found")
        self._thermostat_cluster_handler: ClusterHandler = self.cluster_handlers[
            CLUSTER_HANDLER_THERMOSTAT
        ]
        self._preset: Preset = Preset.NONE
        self._presets: list[Preset] = []
        self._supported_flags = SUPPORT_TARGET_TEMPERATURE
        self._fan_cluster_handler: Optional[ClusterHandler] = self.cluster_handlers.get(
            CLUSTER_HANDLER_FAN
        )
        self._thermostat_cluster_handler.on_event(
            CLUSTER_HANDLER_EVENT, self._handle_event_protocol
        )

    @property
    def current_temperature(self) -> Union[float, None]:
        """Return the current temperature."""
        if self._thermostat_cluster_handler.local_temp is None:
            return None
        return self._thermostat_cluster_handler.local_temp / ZCL_TEMP

    @property
    def extra_state_attributes(self) -> dict:
        """Return device specific state attributes."""
        data = {}
        if self.hvac_mode:
            mode = SYSTEM_MODE_2_HVAC.get(
                self._thermostat_cluster_handler.system_mode, "unknown"
            )
            data[
                ATTR_SYS_MODE
            ] = f"[{self._thermostat_cluster_handler.system_mode}]/{mode}"
        if self._thermostat_cluster_handler.occupancy is not None:
            data[ATTR_OCCUPANCY] = self._thermostat_cluster_handler.occupancy
        if self._thermostat_cluster_handler.occupied_cooling_setpoint is not None:
            data[
                ATTR_OCCP_COOL_SETPT
            ] = self._thermostat_cluster_handler.occupied_cooling_setpoint
        if self._thermostat_cluster_handler.occupied_heating_setpoint is not None:
            data[
                ATTR_OCCP_HEAT_SETPT
            ] = self._thermostat_cluster_handler.occupied_heating_setpoint
        if self._thermostat_cluster_handler.pi_heating_demand is not None:
            data[
                ATTR_PI_HEATING_DEMAND
            ] = self._thermostat_cluster_handler.pi_heating_demand
        if self._thermostat_cluster_handler.pi_cooling_demand is not None:
            data[
                ATTR_PI_COOLING_DEMAND
            ] = self._thermostat_cluster_handler.pi_cooling_demand

        unoccupied_cooling_setpoint = (
            self._thermostat_cluster_handler.unoccupied_cooling_setpoint
        )
        if unoccupied_cooling_setpoint is not None:
            data[ATTR_UNOCCP_COOL_SETPT] = unoccupied_cooling_setpoint

        unoccupied_heating_setpoint = (
            self._thermostat_cluster_handler.unoccupied_heating_setpoint
        )
        if unoccupied_heating_setpoint is not None:
            data[ATTR_UNOCCP_HEAT_SETPT] = unoccupied_heating_setpoint
        return data

    @property
    def fan_mode(self) -> Union[str, None]:
        """Return current FAN mode."""
        if self._thermostat_cluster_handler.running_state is None:
            return FanState.AUTO

        if self._thermostat_cluster_handler.running_state & (
            ThermostatCluster.RunningState.Fan_State_On
            | ThermostatCluster.RunningState.Fan_2nd_Stage_On
            | ThermostatCluster.RunningState.Fan_3rd_Stage_On
        ):
            return FanState.ON
        return FanState.AUTO

    @property
    def fan_modes(self) -> Union[list[str], None]:
        """Return supported FAN modes."""
        if not self._fan_cluster_handler:
            return None
        return [FanState.AUTO, FanState.ON]

    @property
    def hvac_action(self) -> Union[str, None]:
        """Return the current HVAC action."""
        if (
            self._thermostat_cluster_handler.pi_heating_demand is None
            and self._thermostat_cluster_handler.pi_cooling_demand is None
        ):
            return self._rm_rs_action
        return self._pi_demand_action

    @property
    def _rm_rs_action(self) -> Union[str, None]:
        """Return the current HVAC action based on running mode and running state."""

        if (running_state := self._thermostat_cluster_handler.running_state) is None:
            return None
        if running_state & (
            ThermostatCluster.RunningState.Heat_State_On
            | ThermostatCluster.RunningState.Heat_2nd_Stage_On
        ):
            return CurrentHVAC.HEAT
        if running_state & (
            ThermostatCluster.RunningState.Cool_State_On
            | ThermostatCluster.RunningState.Cool_2nd_Stage_On
        ):
            return CurrentHVAC.COOL
        if running_state & (
            ThermostatCluster.RunningState.Fan_State_On
            | ThermostatCluster.RunningState.Fan_2nd_Stage_On
            | ThermostatCluster.RunningState.Fan_3rd_Stage_On
        ):
            return CurrentHVAC.FAN
        if running_state & ThermostatCluster.RunningState.Idle:
            return CurrentHVAC.IDLE
        if self.hvac_mode != HVACMode.OFF:
            return CurrentHVAC.IDLE
        return CurrentHVAC.OFF

    @property
    def _pi_demand_action(self) -> Union[str, None]:
        """Return the current HVAC action based on pi_demands."""

        heating_demand = self._thermostat_cluster_handler.pi_heating_demand
        if heating_demand is not None and heating_demand > 0:
            return CurrentHVAC.HEAT
        cooling_demand = self._thermostat_cluster_handler.pi_cooling_demand
        if cooling_demand is not None and cooling_demand > 0:
            return CurrentHVAC.COOL

        if self.hvac_mode != HVACMode.OFF:
            return CurrentHVAC.IDLE
        return CurrentHVAC.OFF

    @property
    def hvac_mode(self) -> Union[str, None]:
        """Return HVAC operation mode."""
        return SYSTEM_MODE_2_HVAC.get(self._thermostat_cluster_handler.system_mode)

    @property
    def hvac_modes(self) -> tuple[str, ...]:
        """Return the list of available HVAC operation modes."""
        return SEQ_OF_OPERATION.get(
            self._thermostat_cluster_handler.ctrl_seqe_of_oper, (HVACMode.OFF,)
        )

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def preset_mode(self) -> Union[str, None]:
        """Return current preset mode."""
        return self._preset

    @property
    def preset_modes(self) -> Union[list[str], None]:
        """Return supported preset modes."""
        return self._presets

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        features = self._supported_flags
        if HVACMode.HEAT_COOL in self.hvac_modes:
            features |= SUPPORT_TARGET_TEMPERATURE_RANGE
        if self._fan_cluster_handler is not None:
            self._supported_flags |= SUPPORT_FAN_MODE
        return features

    @property
    def target_temperature(self) -> Union[float, None]:
        """Return the temperature we try to reach."""
        temp = None
        if self.hvac_mode == HVACMode.COOL:
            if self.preset_mode == Preset.AWAY:
                temp = self._thermostat_cluster_handler.unoccupied_cooling_setpoint
            else:
                temp = self._thermostat_cluster_handler.occupied_cooling_setpoint
        elif self.hvac_mode == HVACMode.HEAT:
            if self.preset_mode == Preset.AWAY:
                temp = self._thermostat_cluster_handler.unoccupied_heating_setpoint
            else:
                temp = self._thermostat_cluster_handler.occupied_heating_setpoint
        if temp is None:
            return temp
        return round(temp / ZCL_TEMP, 1)

    @property
    def target_temperature_high(self) -> Union[float, None]:
        """Return the upper bound temperature we try to reach."""
        if self.hvac_mode != HVACMode.HEAT_COOL:
            return None
        if self.preset_mode == Preset.AWAY:
            temp = self._thermostat_cluster_handler.unoccupied_cooling_setpoint
        else:
            temp = self._thermostat_cluster_handler.occupied_cooling_setpoint

        if temp is None:
            return temp

        return round(temp / ZCL_TEMP, 1)

    @property
    def target_temperature_low(self) -> Union[float, None]:
        """Return the lower bound temperature we try to reach."""
        if self.hvac_mode != HVACMode.HEAT_COOL:
            return None
        if self.preset_mode == Preset.AWAY:
            temp = self._thermostat_cluster_handler.unoccupied_heating_setpoint
        else:
            temp = self._thermostat_cluster_handler.occupied_heating_setpoint

        if temp is None:
            return temp
        return round(temp / ZCL_TEMP, 1)

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        temps = []
        if HVACMode.HEAT in self.hvac_modes:
            temps.append(self._thermostat_cluster_handler.max_heat_setpoint_limit)
        if HVACMode.COOL in self.hvac_modes:
            temps.append(self._thermostat_cluster_handler.max_cool_setpoint_limit)

        if not temps:
            return self.DEFAULT_MAX_TEMP
        return round(max(temps) / ZCL_TEMP, 1)

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        temps = []
        if HVACMode.HEAT in self.hvac_modes:
            temps.append(self._thermostat_cluster_handler.min_heat_setpoint_limit)
        if HVACMode.COOL in self.hvac_modes:
            temps.append(self._thermostat_cluster_handler.min_cool_setpoint_limit)

        if not temps:
            return self.DEFAULT_MIN_TEMP
        return round(min(temps) / ZCL_TEMP, 1)

    async def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle attribute update from device."""
        if (
            event.name in (ATTR_OCCP_COOL_SETPT, ATTR_OCCP_HEAT_SETPT)
            and self.preset_mode == Preset.AWAY
        ):
            # occupancy attribute is an unreportable attribute, but if we get
            # an attribute update for an "occupied" setpoint, there's a chance
            # occupancy has changed
            if await self._thermostat_cluster_handler.get_occupancy() is True:
                self._preset = Preset.NONE

        self.debug("Attribute '%s' = %s update", event.name, event.value)
        self.maybe_send_state_changed_event()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        if fan_mode not in self.fan_modes:
            self.warning("Unsupported '%s' fan mode", fan_mode)
            return

        if fan_mode == FanState.ON:
            mode = FanCluster.FanMode.On
        else:
            mode = FanCluster.FanMode.Auto

        await self._fan_cluster_handler.async_set_speed(mode)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target operation mode."""
        if hvac_mode not in self.hvac_modes:
            self.warning(
                "can't set '%s' mode. Supported modes are: %s",
                hvac_mode,
                self.hvac_modes,
            )
            return

        if await self._thermostat_cluster_handler.async_set_operation_mode(
            HVAC_MODE_2_SYSTEM[hvac_mode]
        ):
            self.maybe_send_state_changed_event()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes:
            self.debug("preset mode '%s' is not supported", preset_mode)
            return

        if (
            self.preset_mode
            not in (
                preset_mode,
                Preset.NONE,
            )
            and not await self.async_preset_handler(self.preset_mode, enable=False)
        ):
            self.debug("Couldn't turn off '%s' preset", self.preset_mode)
            return

        if preset_mode != Preset.NONE and not await self.async_preset_handler(
            preset_mode, enable=True
        ):
            self.debug("Couldn't turn on '%s' preset", preset_mode)
            return
        self._preset = preset_mode
        self.maybe_send_state_changed_event()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)
        high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temp = kwargs.get(ATTR_TEMPERATURE)
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)

        if hvac_mode is not None:
            await self.async_set_hvac_mode(hvac_mode)

        thrm = self._thermostat_cluster_handler
        if self.hvac_mode == HVACMode.HEAT_COOL:
            success = True
            if low_temp is not None:
                low_temp = int(low_temp * ZCL_TEMP)
                success = success and await thrm.async_set_heating_setpoint(
                    low_temp, self.preset_mode == Preset.AWAY
                )
                self.debug("Setting heating %s setpoint: %s", low_temp, success)
            if high_temp is not None:
                high_temp = int(high_temp * ZCL_TEMP)
                success = success and await thrm.async_set_cooling_setpoint(
                    high_temp, self.preset_mode == Preset.AWAY
                )
                self.debug("Setting cooling %s setpoint: %s", low_temp, success)
        elif temp is not None:
            temp = int(temp * ZCL_TEMP)
            if self.hvac_mode == HVACMode.COOL:
                success = await thrm.async_set_cooling_setpoint(
                    temp, self.preset_mode == Preset.AWAY
                )
            elif self.hvac_mode == HVACMode.HEAT:
                success = await thrm.async_set_heating_setpoint(
                    temp, self.preset_mode == Preset.AWAY
                )
            else:
                self.debug("Not setting temperature for '%s' mode", self.hvac_mode)
                return
        else:
            self.debug("incorrect %s setting for '%s' mode", kwargs, self.hvac_mode)
            return

        if success:
            self.maybe_send_state_changed_event()

    async def async_preset_handler(self, preset: str, enable: bool = False) -> bool:
        """Set the preset mode via handler."""

        handler = getattr(self, f"async_preset_handler_{preset}")
        return await handler(enable)


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_THERMOSTAT, "sinope_manufacturer_specific"},
    manufacturers="Sinope Technologies",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class SinopeTechnologiesThermostat(Thermostat):
    """Sinope Technologies Thermostat."""

    manufacturer = 0x119C
    update_time_interval = (2700, 4500)

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the thermostat."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._presets: list[Preset] = [Preset.AWAY, Preset.NONE]
        self._supported_flags |= SUPPORT_PRESET_MODE
        self._manufacturer_ch: ClusterHandler = self.cluster_handlers[
            "sinope_manufacturer_specific"
        ]

        @periodic(self.update_time_interval)
        async def _update_time() -> None:
            await self._async_update_time()

        self._update_time_task = asyncio.create_task(_update_time())

    @property
    def _rm_rs_action(self) -> Union[str, None]:
        """Return the current HVAC action based on running mode and running state."""

        running_mode = self._thermostat_cluster_handler.running_mode
        if running_mode == ThermostatCluster.SystemMode.Heat:
            return CurrentHVAC.HEAT
        if running_mode == ThermostatCluster.SystemMode.Cool:
            return CurrentHVAC.COOL

        running_state = self._thermostat_cluster_handler.running_state
        if running_state and running_state & (
            ThermostatCluster.RunningState.Fan_State_On
            | ThermostatCluster.RunningState.Fan_2nd_Stage_On
            | ThermostatCluster.RunningState.Fan_3rd_Stage_On
        ):
            return CurrentHVAC.FAN
        if (
            self.hvac_mode != HVACMode.OFF
            and running_mode == ThermostatCluster.SystemMode.Off
        ):
            return CurrentHVAC.IDLE
        return CurrentHVAC.OFF

    async def _async_update_time(self) -> None:
        """Update thermostat's time display."""

        secs_2k = (
            datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            - datetime(2000, 1, 1, 0, 0, 0, 0)
        ).total_seconds()

        self.debug("Updating time: %s", secs_2k)
        try:
            await self._manufacturer_ch.cluster.write_attributes(
                {"secs_since_2k": secs_2k}, manufacturer=self.manufacturer
            )
        except (
            Exception,
            asyncio.CancelledError,
        ) as exc:  # pylint: disable=broad-except
            # Do not print the wrapper in the traceback
            self.warning("Error updating time: %s", exc, exc_info=exc)

    async def async_preset_handler_away(self, is_away: bool = False) -> bool:
        """Set occupancy."""
        mfg_code = self._device.manufacturer_code
        res = await self._thermostat_cluster_handler.write_attributes(
            {"set_occupancy": 0 if is_away else 1}, manufacturer=mfg_code
        )

        self.debug("set occupancy to %s. Status: %s", 0 if is_away else 1, res)
        return res


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    manufacturers="Zen Within",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class ZenWithinThermostat(Thermostat):
    """Zen Within Thermostat implementation."""


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    manufacturers="Centralite",
    models={"3157100", "3157100-E"},
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class CentralitePearl(ZenWithinThermostat):
    """Centralite Pearl Thermostat implementation."""


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    manufacturers={
        "_TZE200_ckud7u2l",
        "_TZE200_ywdxldoj",
        "_TZE200_cwnjrr72",
        "_TZE200_b6wax7g0",
        "_TZE200_2atgpdho",
        "_TZE200_pvvbommb",
        "_TZE200_4eeyebrt",
        "_TYST11_ckud7u2l",
        "_TYST11_ywdxldoj",
        "_TYST11_cwnjrr72",
        "_TYST11_2atgpdho",
    },
)
class MoesThermostat(Thermostat):
    """Moes Thermostat implementation."""

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the thermostat."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._presets: list[Preset] = [
            Preset.NONE,
            Preset.AWAY,
            Preset.SCHEDULE,
            Preset.COMFORT,
            Preset.ECO,
            Preset.BOOST,
            Preset.COMPLEX,
        ]
        self._supported_flags |= SUPPORT_PRESET_MODE

    @property
    def hvac_modes(self) -> tuple[str, ...]:
        """Return only the heat mode, because the device can't be turned off."""
        return (HVACMode.HEAT,)

    async def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle attribute update from device."""
        if event.name == "operation_preset":
            if event.value == 0:
                self._preset = Preset.AWAY
            if event.value == 1:
                self._preset = Preset.SCHEDULE
            if event.value == 2:
                self._preset = Preset.NONE
            if event.value == 3:
                self._preset = Preset.COMFORT
            if event.value == 4:
                self._preset = Preset.ECO
            if event.value == 5:
                self._preset = Preset.BOOST
            if event.value == 6:
                self._preset = Preset.COMPLEX
        await super().handle_cluster_handler_attribute_updated(event)

    async def async_preset_handler(self, preset: str, enable: bool = False) -> bool:
        """Set the preset mode."""
        mfg_code = self._device.manufacturer_code
        if not enable:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 2}, manufacturer=mfg_code
            )
        if preset == Preset.AWAY:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 0}, manufacturer=mfg_code
            )
        if preset == Preset.SCHEDULE:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 1}, manufacturer=mfg_code
            )
        if preset == Preset.COMFORT:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 3}, manufacturer=mfg_code
            )
        if preset == Preset.ECO:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 4}, manufacturer=mfg_code
            )
        if preset == Preset.BOOST:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 5}, manufacturer=mfg_code
            )
        if preset == Preset.COMPLEX:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 6}, manufacturer=mfg_code
            )

        return False


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    manufacturers={
        "_TZE200_b6wax7g0",
    },
)
class BecaThermostat(Thermostat):
    """Beca Thermostat implementation."""

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the thermostat."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._presets: list[Preset] = [
            Preset.NONE,
            Preset.AWAY,
            Preset.SCHEDULE,
            Preset.ECO,
            Preset.BOOST,
            Preset.TEMP_MANUAL,
        ]
        self._supported_flags |= SUPPORT_PRESET_MODE

    @property
    def hvac_modes(self) -> tuple[str, ...]:
        """Return only the heat mode, because the device can't be turned off."""
        return (HVACMode.HEAT,)

    async def handle_cluster_handler_attribute_updated(
        self, event: ClusterAttributeUpdatedEvent
    ) -> None:
        """Handle attribute update from device."""
        if event.name == "operation_preset":
            if event.value == 0:
                self._preset = Preset.AWAY
            if event.value == 1:
                self._preset = Preset.SCHEDULE
            if event.value == 2:
                self._preset = Preset.NONE
            if event.value == 4:
                self._preset = Preset.ECO
            if event.value == 5:
                self._preset = Preset.BOOST
            if event.value == 7:
                self._preset = Preset.TEMP_MANUAL
        await super().handle_cluster_handler_attribute_updated(event)

    async def async_preset_handler(self, preset: str, enable: bool = False) -> bool:
        """Set the preset mode."""
        mfg_code = self._device.manufacturer_code
        if not enable:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 2}, manufacturer=mfg_code
            )
        if preset == Preset.AWAY:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 0}, manufacturer=mfg_code
            )
        if preset == Preset.SCHEDULE:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 1}, manufacturer=mfg_code
            )
        if preset == Preset.ECO:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 4}, manufacturer=mfg_code
            )
        if preset == Preset.BOOST:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 5}, manufacturer=mfg_code
            )
        if preset == Preset.TEMP_MANUAL:
            return await self._thermostat_cluster_handler.write_attributes(
                {"operation_preset": 7}, manufacturer=mfg_code
            )

        return False
