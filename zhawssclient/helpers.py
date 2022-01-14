"""Helper classes for zhawssclient."""

from typing import Awaitable, Literal, Optional, Union

from zhawssclient.client import Client
from zhawssclient.model.commands import (
    AlarmControlPanelArmAwayCommand,
    AlarmControlPanelArmHomeCommand,
    AlarmControlPanelArmNightCommand,
    AlarmControlPanelDisarmCommand,
    AlarmControlPanelTriggerCommand,
    ButtonPressCommand,
    ClimateSetFanModeCommand,
    ClimateSetHvacModeCommand,
    ClimateSetPresetModeCommand,
    ClimateSetTemperatureCommand,
    CoverCloseCommand,
    CoverOpenCommand,
    CoverSetPositionCommand,
    CoverStopCommand,
    FanSetPercentageCommand,
    FanSetPresetModeCommand,
    FanTurnOffCommand,
    FanTurnOnCommand,
    LightTurnOffCommand,
    LightTurnOnCommand,
    LockClearUserLockCodeCommand,
    LockDisableUserLockCodeCommand,
    LockEnableUserLockCodeCommand,
    LockLockCommand,
    LockSetUserLockCodeCommand,
    LockUnlockCommand,
    NumberSetValueCommand,
    PlatformEntityRefreshStateCommand,
    SelectSelectOptionCommand,
    SirenTurnOffCommand,
    SirenTurnOnCommand,
    SwitchTurnOffCommand,
    SwitchTurnOnCommand,
)
from zhawssclient.model.types import ControllerType


class LightHelper:
    """Helper to issue light commands."""

    CONTROLLER_ATTRIBUTE = "lights"

    def __init__(self, client: Client):
        """Initialize the light helper."""
        self._client: Client = client

    async def turn_on(
        self,
        light_platform_entity,
        brightness=None,
        transition=None,
        flash=None,
        effect=None,
        hs_color=None,
        color_temp=None,
    ) -> Awaitable[None]:
        """Turn on a light."""
        if light_platform_entity is None or light_platform_entity.platform != "LIGHT":
            raise ValueError(
                "light_platform_entity must be provided and it must be a light platform entity"
            )

        command = LightTurnOnCommand(
            ieee=light_platform_entity.device_ieee,
            unique_id=light_platform_entity.unique_id,
            brightness=brightness,
            transition=transition,
            flash=flash,
            effect=effect,
            hs_color=hs_color,
            color_temp=color_temp,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(
        self, light_platform_entity, transition=None, flash=None
    ) -> Awaitable[None]:
        """Turn off a light."""
        if light_platform_entity is None or light_platform_entity.platform != "LIGHT":
            raise ValueError(
                "light_platform_entity must be provided and it must be a light platform entity"
            )

        command = LightTurnOffCommand(
            ieee=light_platform_entity.device_ieee,
            unique_id=light_platform_entity.unique_id,
            transition=transition,
            flash=flash,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SwitchHelper:
    """Helper to issue switch commands."""

    CONTROLLER_ATTRIBUTE = "switches"

    def __init__(self, client: Client):
        """Initialize the switch helper."""
        self._client: Client = client

    async def turn_on(self, switch_platform_entity) -> Awaitable[None]:
        """Turn on a switch."""
        if (
            switch_platform_entity is None
            or switch_platform_entity.platform != "SWITCH"
        ):
            raise ValueError(
                "switch_platform_entity must be provided and it must be a switch platform entity"
            )

        command = SwitchTurnOnCommand(
            ieee=switch_platform_entity.device_ieee,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(self, switch_platform_entity) -> Awaitable[None]:
        """Turn off a switch."""
        if (
            switch_platform_entity is None
            or switch_platform_entity.platform != "SWITCH"
        ):
            raise ValueError(
                "switch_platform_entity must be provided and it must be a switch platform entity"
            )

        command = SwitchTurnOffCommand(
            ieee=switch_platform_entity.device_ieee,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SirenHelper:
    """Helper to issue siren commands."""

    CONTROLLER_ATTRIBUTE = "sirens"

    def __init__(self, client: Client):
        """Initialize the siren helper."""
        self._client: Client = client

    async def turn_on(
        self,
        siren_platform_entity,
        duration: Optional[int] = None,
        volume_level: Optional[int] = None,
        tone: Optional[str] = None,
    ) -> Awaitable[None]:
        """Turn on a siren."""
        if siren_platform_entity is None or siren_platform_entity.platform != "SIREN":
            raise ValueError(
                "siren_platform_entity must be provided and it must be a siren platform entity"
            )

        command = SirenTurnOnCommand(
            ieee=siren_platform_entity.device_ieee,
            unique_id=siren_platform_entity.unique_id,
            duration=duration,
            volume_level=volume_level,
            tone=tone,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(self, siren_platform_entity) -> Awaitable[None]:
        """Turn off a siren."""
        if siren_platform_entity is None or siren_platform_entity.platform != "SIREN":
            raise ValueError(
                "siren_platform_entity must be provided and it must be a siren platform entity"
            )

        command = SirenTurnOffCommand(
            ieee=siren_platform_entity.device_ieee,
            unique_id=siren_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class ButtonHelper:
    """Helper to issue button commands."""

    CONTROLLER_ATTRIBUTE = "buttons"

    def __init__(self, client: Client):
        """Initialize the button helper."""
        self._client: Client = client

    async def press(self, button_platform_entity) -> Awaitable[None]:
        """Press a button."""
        if (
            button_platform_entity is None
            or button_platform_entity.platform != "BUTTON"
        ):
            raise ValueError(
                "button_platform_entity must be provided and it must be a button platform entity"
            )

        command = ButtonPressCommand(
            ieee=button_platform_entity.device_ieee,
            unique_id=button_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class CoverHelper:
    """helper to issue cover commands"""

    CONTROLLER_ATTRIBUTE = "covers"

    def __init__(self, client: Client):
        """Initialize the cover helper."""
        self._client: Client = client

    async def open_cover(self, cover_platform_entity) -> Awaitable[None]:
        """Open a cover."""
        if cover_platform_entity is None or cover_platform_entity.platform != "COVER":
            raise ValueError(
                "cover_platform_entity must be provided and it must be a cover platform entity"
            )

        command = CoverOpenCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def close_cover(self, cover_platform_entity) -> Awaitable[None]:
        """Close a cover."""
        if cover_platform_entity is None or cover_platform_entity.platform != "COVER":
            raise ValueError(
                "cover_platform_entity must be provided and it must be a cover platform entity"
            )

        command = CoverCloseCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def stop_cover(self, cover_platform_entity) -> Awaitable[None]:
        """Stop a cover."""
        if cover_platform_entity is None or cover_platform_entity.platform != "COVER":
            raise ValueError(
                "cover_platform_entity must be provided and it must be a cover platform entity"
            )

        command = CoverStopCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_cover_position(
        self,
        cover_platform_entity,
        position: int,
    ) -> Awaitable[None]:
        """Set a cover position."""
        if cover_platform_entity is None or cover_platform_entity.platform != "COVER":
            raise ValueError(
                "cover_platform_entity must be provided and it must be a cover platform entity"
            )

        command = CoverSetPositionCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
            position=position,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class FanHelper:
    """Helper to issue fan commands."""

    CONTROLLER_ATTRIBUTE = "fans"

    def __init__(self, client: Client):
        """Initialize the fan helper."""
        self._client: Client = client

    async def turn_on(
        self,
        fan_platform_entity,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
    ) -> Awaitable[None]:
        """Turn on a fan."""
        if fan_platform_entity is None or fan_platform_entity.platform != "FAN":
            raise ValueError(
                "fan_platform_entity must be provided and it must be a fan platform entity"
            )

        command = FanTurnOnCommand(
            ieee=fan_platform_entity.device_ieee,
            unique_id=fan_platform_entity.unique_id,
            speed=speed,
            percentage=percentage,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(self, fan_platform_entity) -> Awaitable[None]:
        """Turn off a fan."""
        if fan_platform_entity is None or fan_platform_entity.platform != "FAN":
            raise ValueError(
                "fan_platform_entity must be provided and it must be a fan platform entity"
            )

        command = FanTurnOffCommand(
            ieee=fan_platform_entity.device_ieee,
            unique_id=fan_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_fan_percentage(
        self,
        fan_platform_entity,
        percentage: int,
    ) -> Awaitable[None]:
        """Set a fan percentage."""
        if fan_platform_entity is None or fan_platform_entity.platform != "FAN":
            raise ValueError(
                "fan_platform_entity must be provided and it must be a fan platform entity"
            )

        command = FanSetPercentageCommand(
            ieee=fan_platform_entity.device_ieee,
            unique_id=fan_platform_entity.unique_id,
            percentage=percentage,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_fan_preset_mode(
        self,
        fan_platform_entity,
        preset_mode: str,
    ) -> Awaitable[None]:
        """Set a fan preset mode."""
        if fan_platform_entity is None or fan_platform_entity.platform != "FAN":
            raise ValueError(
                "fan_platform_entity must be provided and it must be a fan platform entity"
            )

        command = FanSetPresetModeCommand(
            ieee=fan_platform_entity.device_ieee,
            unique_id=fan_platform_entity.unique_id,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class LockHelper:
    """Helper to issue lock commands."""

    CONTROLLER_ATTRIBUTE = "locks"

    def __init__(self, client: Client):
        """Initialize the lock helper."""
        self._client: Client = client

    async def lock(self, lock_platform_entity) -> Awaitable[None]:
        """Lock a lock."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockLockCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def unlock(self, lock_platform_entity) -> Awaitable[None]:
        """Unlock a lock."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockUnlockCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_user_lock_code(
        self,
        lock_platform_entity,
        code_slot: int,
        user_code: str,
    ) -> Awaitable[None]:
        """Set a user lock code."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockSetUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
            user_code=user_code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def clear_user_lock_code(
        self,
        lock_platform_entity,
        code_slot: int,
    ) -> Awaitable[None]:
        """Clear a user lock code."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockClearUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def enable_user_lock_code(
        self,
        lock_platform_entity,
        code_slot: int,
    ) -> Awaitable[None]:
        """Enable a user lock code."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockEnableUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def disable_user_lock_code(
        self,
        lock_platform_entity,
        code_slot: int,
    ) -> Awaitable[None]:
        """Disable a user lock code."""
        if lock_platform_entity is None or lock_platform_entity.platform != "LOCK":
            raise ValueError(
                "lock_platform_entity must be provided and it must be a lock platform entity"
            )

        command = LockDisableUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class NumberHelper:
    """Helper to issue number commands."""

    CONTROLLER_ATTRIBUTE = "numbers"

    def __init__(self, client: Client):
        """Initialize the number helper."""
        self._client: Client = client

    async def set_value(
        self,
        number_platform_entity,
        value: Union[int, float],
    ) -> Awaitable[None]:
        """Set a number."""
        if (
            number_platform_entity is None
            or number_platform_entity.platform != "NUMBER"
        ):
            raise ValueError(
                "number_platform_entity must be provided and it must be a number platform entity"
            )

        command = NumberSetValueCommand(
            ieee=number_platform_entity.device_ieee,
            unique_id=number_platform_entity.unique_id,
            value=value,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SelectHelper:
    """Helper to issue select commands."""

    CONTROLLER_ATTRIBUTE = "selects"

    def __init__(self, client: Client):
        """Initialize the select helper."""
        self._client: Client = client

    async def select_option(
        self,
        select_platform_entity,
        option: Union[str, int],
    ) -> Awaitable[None]:
        """Set a select."""
        if (
            select_platform_entity is None
            or select_platform_entity.platform != "SELECT"
        ):
            raise ValueError(
                "select_platform_entity must be provided and it must be a select platform entity"
            )

        command = SelectSelectOptionCommand(
            ieee=select_platform_entity.device_ieee,
            unique_id=select_platform_entity.unique_id,
            option=option,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class ClimateHelper:
    """Helper to issue climate commands."""

    CONTROLLER_ATTRIBUTE = "climates"

    def __init__(self, client: Client):
        """Initialize the climate helper."""
        self._client: Client = client

    async def set_hvac_mode(
        self,
        climate_platform_entity,
        hvac_mode: Literal[
            "heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"
        ],
    ) -> Awaitable[None]:
        """Set a climate."""
        if (
            climate_platform_entity is None
            or climate_platform_entity.platform != "CLIMATE"
        ):
            raise ValueError(
                "climate_platform_entity must be provided and it must be a climate platform entity"
            )

        command = ClimateSetHvacModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            hvac_mode=hvac_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_temperature(
        self,
        climate_platform_entity,
        hvac_mode: Optional[
            Literal["heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"]
        ] = None,
        temperature: Optional[float] = None,
        target_temp_high: Optional[float] = None,
        target_temp_low: Optional[float] = None,
    ) -> Awaitable[None]:
        """Set a climate."""
        if (
            climate_platform_entity is None
            or climate_platform_entity.platform != "CLIMATE"
        ):
            raise ValueError(
                "climate_platform_entity must be provided and it must be a climate platform entity"
            )

        command = ClimateSetTemperatureCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            temperature=temperature,
            target_temp_high=target_temp_high,
            target_temp_low=target_temp_low,
            hvac_mode=hvac_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_fan_mode(
        self,
        climate_platform_entity,
        fan_mode: str,
    ) -> Awaitable[None]:
        """Set a climate."""
        if (
            climate_platform_entity is None
            or climate_platform_entity.platform != "CLIMATE"
        ):
            raise ValueError(
                "climate_platform_entity must be provided and it must be a climate platform entity"
            )

        command = ClimateSetFanModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            fan_mode=fan_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_preset_mode(
        self,
        climate_platform_entity,
        preset_mode: str,
    ) -> Awaitable[None]:
        """Set a climate."""
        if (
            climate_platform_entity is None
            or climate_platform_entity.platform != "CLIMATE"
        ):
            raise ValueError(
                "climate_platform_entity must be provided and it must be a climate platform entity"
            )

        command = ClimateSetPresetModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class AlarmControlPanelHelper:
    """Helper to issue alarm control panel commands."""

    CONTROLLER_ATTRIBUTE = "alarm_control_panels"

    def __init__(self, client: Client):
        """Initialize the alarm control panel helper."""
        self._client: Client = client

    async def disarm(
        self, alarm_control_panel_platform_entity, code: str
    ) -> Awaitable[None]:
        """Disarm an alarm control panel."""
        if (
            alarm_control_panel_platform_entity is None
            or alarm_control_panel_platform_entity.platform != "ALARM_CONTROL_PANEL"
        ):
            raise ValueError(
                "alarm_control_panel_platform_entity must be provided and it must be an alarm control panel platform entity"
            )

        command = AlarmControlPanelDisarmCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_home(
        self, alarm_control_panel_platform_entity, code: str
    ) -> Awaitable[None]:
        """Arm an alarm control panel in home mode."""
        if (
            alarm_control_panel_platform_entity is None
            or alarm_control_panel_platform_entity.platform != "ALARM_CONTROL_PANEL"
        ):
            raise ValueError(
                "alarm_control_panel_platform_entity must be provided and it must be an alarm control panel platform entity"
            )

        command = AlarmControlPanelArmHomeCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_away(
        self, alarm_control_panel_platform_entity, code: str
    ) -> Awaitable[None]:
        """Arm an alarm control panel in away mode."""
        if (
            alarm_control_panel_platform_entity is None
            or alarm_control_panel_platform_entity.platform != "ALARM_CONTROL_PANEL"
        ):
            raise ValueError(
                "alarm_control_panel_platform_entity must be provided and it must be an alarm control panel platform entity"
            )

        command = AlarmControlPanelArmAwayCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_night(
        self, alarm_control_panel_platform_entity, code: str
    ) -> Awaitable[None]:
        """Arm an alarm control panel in night mode."""
        if (
            alarm_control_panel_platform_entity is None
            or alarm_control_panel_platform_entity.platform != "ALARM_CONTROL_PANEL"
        ):
            raise ValueError(
                "alarm_control_panel_platform_entity must be provided and it must be an alarm control panel platform entity"
            )

        command = AlarmControlPanelArmNightCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def trigger(
        self,
        alarm_control_panel_platform_entity,
    ) -> Awaitable[None]:
        """Trigger an alarm control panel alarm."""
        if (
            alarm_control_panel_platform_entity is None
            or alarm_control_panel_platform_entity.platform != "ALARM_CONTROL_PANEL"
        ):
            raise ValueError(
                "alarm_control_panel_platform_entity must be provided and it must be an alarm control panel platform entity"
            )

        command = AlarmControlPanelTriggerCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class PlatformEntityHelper:
    """Helper to get platform entities."""

    CONTROLLER_ATTRIBUTE = "entities"

    def __init__(self, client: Client):
        """Initialize the platform entity helper."""
        self._client: Client = client

    async def refresh_state(self, platform_entity) -> Awaitable[None]:
        """Refresh the state of a platform entity."""
        command = PlatformEntityRefreshStateCommand(
            ieee=platform_entity.device_ieee,
            unique_id=platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


def attach_platform_entity_helpers(controller: ControllerType, client: Client) -> None:
    """Attach helper methods to the controller."""
    setattr(controller, LightHelper.CONTROLLER_ATTRIBUTE, LightHelper(client))
    setattr(controller, SwitchHelper.CONTROLLER_ATTRIBUTE, SwitchHelper(client))
    setattr(controller, SirenHelper.CONTROLLER_ATTRIBUTE, SirenHelper(client))
    setattr(controller, ButtonHelper.CONTROLLER_ATTRIBUTE, ButtonHelper(client))
    setattr(controller, CoverHelper.CONTROLLER_ATTRIBUTE, CoverHelper(client))
    setattr(controller, FanHelper.CONTROLLER_ATTRIBUTE, FanHelper(client))
    setattr(controller, LockHelper.CONTROLLER_ATTRIBUTE, LockHelper(client))
    setattr(controller, NumberHelper.CONTROLLER_ATTRIBUTE, NumberHelper(client))
    setattr(controller, SelectHelper.CONTROLLER_ATTRIBUTE, SelectHelper(client))
    setattr(controller, ClimateHelper.CONTROLLER_ATTRIBUTE, ClimateHelper(client))
    setattr(
        controller,
        AlarmControlPanelHelper.CONTROLLER_ATTRIBUTE,
        AlarmControlPanelHelper(client),
    )
    setattr(
        controller,
        PlatformEntityHelper.CONTROLLER_ATTRIBUTE,
        PlatformEntityHelper(client),
    )
