"""Models that represent commands and command responses."""

from typing import Annotated, Dict, Literal, Optional, Tuple, Union

from pydantic import conint
from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.types import Device


class Command(BaseModel):
    """Base class for command that are sent to the server."""

    command: str


class DeviceCommand(Command):
    """Base class for commands that address individual devices."""

    ieee: str


class PlatformEntityCommand(DeviceCommand):
    """Base class for commands that address individual platform entities."""

    unique_id: str


class LightTurnOnCommand(PlatformEntityCommand):
    """Command to instruct a light to turn on."""

    command: Literal["light_turn_on"] = "light_turn_on"
    brightness: Optional[int]
    transition: Optional[int]
    flash: Optional[Literal["long", "short"]]
    effect: Optional[str]
    hs_color: Optional[Tuple[float, float]]
    color_temp: Optional[int]


class LightTurnOffCommand(PlatformEntityCommand):
    """Command to instruct a light to turn off."""

    command: Literal["light_turn_off"] = "light_turn_off"
    transition: Optional[int]
    flash: Optional[Literal["long", "short"]]


class SwitchTurnOnCommand(PlatformEntityCommand):
    """Command to instruct a switch to turn on."""

    command: Literal["switch_turn_on"] = "switch_turn_on"


class SwitchTurnOffCommand(PlatformEntityCommand):
    """Command to instruct a switch to turn off."""

    command: Literal["switch_turn_off"] = "switch_turn_off"


class SirenTurnOffCommand(PlatformEntityCommand):
    """Command to instruct a siren to turn off."""

    command: Literal["siren_turn_off"] = "siren_turn_off"


class SelectSelectOptionCommand(PlatformEntityCommand):
    """Command to instruct a select an option for a select platform entity."""

    command: Literal["select_select_option"] = "select_select_option"
    option: Union[str, int]


class NumberSetValueCommand(PlatformEntityCommand):
    """Command to set the value of a number platform entity."""

    command: Literal["number_set_value"] = "number_set_value"
    value: Union[float, int]


class SirenTurnOnCommand(PlatformEntityCommand):
    """Command to instruct a siren to turn off."""

    command: Literal["siren_turn_on"] = "siren_turn_on"
    duration: Optional[int]
    volume_level: Optional[int]
    tone: Optional[str]


class LockLockCommand(PlatformEntityCommand):
    """Command to lock a lock platform entity."""

    command: Literal["lock_lock"] = "lock_lock"


class LockUnlockCommand(PlatformEntityCommand):
    """Command to unlock a lock platform entity."""

    command: Literal["lock_unlock"] = "lock_unlock"


class LockDisableUserLockCodeCommand(PlatformEntityCommand):
    """Command to lock a lock platform entity."""

    command: Literal["lock_disable_user_lock_code"] = "lock_disable_user_lock_code"
    code_slot: int


class LockSetUserLockCodeCommand(PlatformEntityCommand):
    """Command to lock a lock platform entity."""

    command: Literal["lock_set_user_lock_code"] = "lock_set_user_lock_code"
    code_slot: int
    user_code: str


class LockEnableUserLockCodeCommand(PlatformEntityCommand):
    """Command to lock a lock platform entity."""

    command: Literal["lock_enable_user_lock_code"] = "lock_enable_user_lock_code"
    code_slot: int


class LockClearUserLockCodeCommand(PlatformEntityCommand):
    """Command to lock a lock platform entity."""

    command: Literal["lock_clear_user_lock_code"] = "lock_clear_user_lock_code"
    code_slot: int


class FanTurnOnCommand(PlatformEntityCommand):
    """Command to turn on a fan platform entity."""

    command: Literal["fan_turn_on"] = "fan_turn_on"
    speed: Optional[str]
    percentage: Optional[conint(ge=0, le=100)]
    preset_mode: Optional[str]


class FanTurnOffCommand(PlatformEntityCommand):
    """Command to turn off a fan platform entity."""

    command: Literal["fan_turn_off"] = "fan_turn_off"


class FanSetPercentageCommand(PlatformEntityCommand):
    """Command to set the speed percentage for a fan platform entity."""

    command: Literal["fan_set_percentage"] = "fan_set_percentage"
    percentage: Optional[conint(ge=0, le=100)]


class FanSetPresetModeCommand(PlatformEntityCommand):
    """Command to set the preset mode for a fan platform entity."""

    command: Literal["fan_set_preset_mode"] = "fan_set_preset_mode"
    preset_mode: Optional[str]


class CoverOpenCommand(PlatformEntityCommand):
    """Command to open a cover platform entity."""

    command: Literal["cover_open"] = "cover_open"


class CoverCloseCommand(PlatformEntityCommand):
    """Command to open a cover platform entity."""

    command: Literal["cover_close"] = "cover_close"


class CoverSetPositionCommand(PlatformEntityCommand):
    """Command to set the position of a cover platform entity."""

    command: Literal["cover_set_position"] = "cover_set_position"
    position: int


class CoverStopCommand(PlatformEntityCommand):
    """Command to stop a cover platform entity."""

    command: Literal["cover_stop"] = "cover_stop"


class ClimateSetFanModeCommand(PlatformEntityCommand):
    """Command to set the fan mode for a climate platform entity."""

    command: Literal["climate_set_fan_mode"] = "climate_set_fan_mode"
    fan_mode: Optional[str]


class ClimateSetHvacModeCommand(PlatformEntityCommand):
    """Command to set the hvac mode for a climate platform entity."""

    command: Literal["climate_set_hvac_mode"] = "climate_set_hvac_mode"
    hvac_mode: Literal["heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"]


class ClimateSetPresetModeCommand(PlatformEntityCommand):
    """Command to set the preset mode for a climate platform entity."""

    command: Literal["climate_set_preset_mode"] = "climate_set_preset_mode"
    preset_mode: Optional[str]


class ClimateSetTemperatureCommand(PlatformEntityCommand):
    """Command to set the temperature for a climate platform entity."""

    command: Literal["climate_set_preset_mode"] = "climate_set_preset_mode"
    hvac_mode: Optional[
        Literal["heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"]
    ]
    temperature: Optional[float]
    target_temp_high: Optional[float]
    target_temp_low: Optional[float]


class ButtonPressCommand(PlatformEntityCommand):
    """Command to issue the press command for a button platform entity."""

    command: Literal["button_press"] = "button_press"


class AlarmControlPanelDisarmCommand(PlatformEntityCommand):
    """Command to disarm an alarm control panel platform entity."""

    command: Literal["alarm_control_panel_disarm"] = "alarm_control_panel_disarm"
    code: str


class AlarmControlPanelArmHomeCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in home mode."""

    command: Literal["alarm_control_panel_arm_home"] = "alarm_control_panel_arm_home"
    code: str


class AlarmControlPanelArmAwayCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in away mode."""

    command: Literal["alarm_control_panel_arm_away"] = "alarm_control_panel_arm_away"
    code: str


class AlarmControlPanelArmNightCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in night mode."""

    command: Literal["alarm_control_panel_arm_night"] = "alarm_control_panel_arm_night"
    code: str


class AlarmControlPanelTriggerCommand(PlatformEntityCommand):
    """Command to trigger the alarm for an alarm control panel platform entity."""

    command: Literal["alarm_control_panel_trigger"] = "alarm_control_panel_trigger"


class CommandResponse(BaseModel):
    """Command response model."""

    message_type: Literal["result"] = "result"
    message_id: int
    success: bool


class DefaultResponse(CommandResponse):
    """Get devices response."""

    command: Literal[
        "start_network",
        "stop_network",
        "remove_device",
        "stop_server",
        "light_turn_on",
        "light_turn_off",
        "switch_turn_on",
        "switch_turn_off",
        "lock_lock",
        "lock_unlock",
        "lock_set_user_lock_code",
        "lock_clear_user_lock_code",
        "lock_disable_user_lock_code",
        "lock_enable_user_lock_code",
        "fan_turn_on",
        "fan_turn_off",
        "fan_set_percentage",
        "fan_set_preset_mode",
        "cover_open",
        "cover_close",
        "cover_set_position",
        "cover_stop",
        "climate_set_fan_mode",
        "climate_set_hvac_mode",
        "climate_set_preset_mode",
        "climate_set_temperature",
        "button_press",
        "alarm_control_panel_disarm",
        "alarm_control_panel_arm_home",
        "alarm_control_panel_arm_away",
        "alarm_control_panel_arm_night",
        "alarm_control_panel_trigger",
        "select_select_option",
        "siren_turn_on",
        "siren_turn_off",
        "numbet_set_value",
    ]


class PermitJoiningResponse(CommandResponse):
    """Get devices response."""

    command: Literal["permit_joining"] = "permit_joining"
    duration: int


class GetDevicesResponse(CommandResponse):
    """Get devices response."""

    command: Literal["get_devices"] = "get_devices"
    devices: Dict[str, Device] = None


CommandResponses = Annotated[
    Union[DefaultResponse, GetDevicesResponse, PermitJoiningResponse],
    Field(discriminator="command"),  # noqa: F821
]
