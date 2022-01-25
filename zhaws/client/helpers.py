"""Helper classes for zhaws.client."""
from __future__ import annotations

from typing import Any, Literal, Optional, Union, cast

from zhaws.client.client import Client
from zhaws.client.model.commands import (
    AddGroupMembersCommand,
    AlarmControlPanelArmAwayCommand,
    AlarmControlPanelArmHomeCommand,
    AlarmControlPanelArmNightCommand,
    AlarmControlPanelDisarmCommand,
    AlarmControlPanelTriggerCommand,
    ButtonPressCommand,
    ClientDisconnectCommand,
    ClientListenCommand,
    ClientListenRawZCLCommand,
    ClimateSetFanModeCommand,
    ClimateSetHvacModeCommand,
    ClimateSetPresetModeCommand,
    ClimateSetTemperatureCommand,
    CommandResponse,
    CoverCloseCommand,
    CoverOpenCommand,
    CoverSetPositionCommand,
    CoverStopCommand,
    CreateGroupCommand,
    FanSetPercentageCommand,
    FanSetPresetModeCommand,
    FanTurnOffCommand,
    FanTurnOnCommand,
    GetDevicesCommand,
    GetDevicesResponse,
    GetGroupsCommand,
    GroupsResponse,
    LightTurnOffCommand,
    LightTurnOnCommand,
    LockClearUserLockCodeCommand,
    LockDisableUserLockCodeCommand,
    LockEnableUserLockCodeCommand,
    LockLockCommand,
    LockSetUserLockCodeCommand,
    LockUnlockCommand,
    NumberSetValueCommand,
    PermitJoiningCommand,
    PermitJoiningResponse,
    PlatformEntityRefreshStateCommand,
    ReadClusterAttributesCommand,
    ReadClusterAttributesResponse,
    ReconfigureDeviceCommand,
    RemoveGroupMembersCommand,
    RemoveGroupsCommand,
    SelectSelectOptionCommand,
    SirenTurnOffCommand,
    SirenTurnOnCommand,
    StartNetworkCommand,
    StopNetworkCommand,
    StopServerCommand,
    SwitchTurnOffCommand,
    SwitchTurnOnCommand,
    UpdateGroupResponse,
    UpdateNetworkTopologyCommand,
    WriteClusterAttributeCommand,
    WriteClusterAttributeResponse,
)
from zhaws.client.model.types import (
    BaseEntity,
    BasePlatformEntity,
    Device,
    Group,
    GroupEntity,
)
from zhaws.server.platforms.registries import Platform


def ensure_platform_entity(entity: BaseEntity, platform: Platform) -> None:
    """Ensure an entity exists and is from the specified platform."""
    if entity is None or entity.platform != platform:
        raise ValueError(
            f"entity must be provided and it must be a {platform} platform entity"
        )


class LightHelper:
    """Helper to issue light commands."""

    def __init__(self, client: Client):
        """Initialize the light helper."""
        self._client: Client = client

    async def turn_on(
        self,
        light_platform_entity: BasePlatformEntity | GroupEntity,
        brightness: int | None = None,
        transition: int | None = None,
        flash: bool | None = None,
        effect: str | None = None,
        hs_color: tuple | None = None,
        color_temp: int | None = None,
    ) -> CommandResponse:
        """Turn on a light."""
        ensure_platform_entity(light_platform_entity, Platform.LIGHT)
        command = LightTurnOnCommand(
            ieee=light_platform_entity.device_ieee
            if not isinstance(light_platform_entity, GroupEntity)
            else None,
            group_id=light_platform_entity.group_id
            if isinstance(light_platform_entity, GroupEntity)
            else None,
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
        self,
        light_platform_entity: BasePlatformEntity | GroupEntity,
        transition: int | None = None,
        flash: bool | None = None,
    ) -> CommandResponse:
        """Turn off a light."""
        ensure_platform_entity(light_platform_entity, Platform.LIGHT)
        command = LightTurnOffCommand(
            ieee=light_platform_entity.device_ieee
            if not isinstance(light_platform_entity, GroupEntity)
            else None,
            group_id=light_platform_entity.group_id
            if isinstance(light_platform_entity, GroupEntity)
            else None,
            unique_id=light_platform_entity.unique_id,
            transition=transition,
            flash=flash,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SwitchHelper:
    """Helper to issue switch commands."""

    def __init__(self, client: Client):
        """Initialize the switch helper."""
        self._client: Client = client

    async def turn_on(
        self,
        switch_platform_entity: BasePlatformEntity | GroupEntity,
    ) -> CommandResponse:
        """Turn on a switch."""
        ensure_platform_entity(switch_platform_entity, Platform.SWITCH)
        command = SwitchTurnOnCommand(
            ieee=switch_platform_entity.device_ieee
            if not isinstance(switch_platform_entity, GroupEntity)
            else None,
            group_id=switch_platform_entity.group_id
            if isinstance(switch_platform_entity, GroupEntity)
            else None,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(
        self,
        switch_platform_entity: BasePlatformEntity | GroupEntity,
    ) -> CommandResponse:
        """Turn off a switch."""
        ensure_platform_entity(switch_platform_entity, Platform.SWITCH)
        command = SwitchTurnOffCommand(
            ieee=switch_platform_entity.device_ieee
            if not isinstance(switch_platform_entity, GroupEntity)
            else None,
            group_id=switch_platform_entity.group_id
            if isinstance(switch_platform_entity, GroupEntity)
            else None,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SirenHelper:
    """Helper to issue siren commands."""

    def __init__(self, client: Client):
        """Initialize the siren helper."""
        self._client: Client = client

    async def turn_on(
        self,
        siren_platform_entity: BasePlatformEntity,
        duration: Optional[int] = None,
        volume_level: Optional[int] = None,
        tone: Optional[str] = None,
    ) -> CommandResponse:
        """Turn on a siren."""
        ensure_platform_entity(siren_platform_entity, Platform.SIREN)
        command = SirenTurnOnCommand(
            ieee=siren_platform_entity.device_ieee,
            unique_id=siren_platform_entity.unique_id,
            duration=duration,
            volume_level=volume_level,
            tone=tone,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(
        self, siren_platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Turn off a siren."""
        ensure_platform_entity(siren_platform_entity, Platform.SIREN)
        command = SirenTurnOffCommand(
            ieee=siren_platform_entity.device_ieee,
            unique_id=siren_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class ButtonHelper:
    """Helper to issue button commands."""

    def __init__(self, client: Client):
        """Initialize the button helper."""
        self._client: Client = client

    async def press(
        self, button_platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Press a button."""
        ensure_platform_entity(button_platform_entity, Platform.BUTTON)
        command = ButtonPressCommand(
            ieee=button_platform_entity.device_ieee,
            unique_id=button_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class CoverHelper:
    """helper to issue cover commands"""

    def __init__(self, client: Client):
        """Initialize the cover helper."""
        self._client: Client = client

    async def open_cover(
        self, cover_platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Open a cover."""
        ensure_platform_entity(cover_platform_entity, Platform.COVER)
        command = CoverOpenCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def close_cover(
        self, cover_platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Close a cover."""
        ensure_platform_entity(cover_platform_entity, Platform.COVER)
        command = CoverCloseCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def stop_cover(
        self, cover_platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Stop a cover."""
        ensure_platform_entity(cover_platform_entity, Platform.COVER)
        command = CoverStopCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_cover_position(
        self,
        cover_platform_entity: BasePlatformEntity,
        position: int,
    ) -> CommandResponse:
        """Set a cover position."""
        ensure_platform_entity(cover_platform_entity, Platform.COVER)
        command = CoverSetPositionCommand(
            ieee=cover_platform_entity.device_ieee,
            unique_id=cover_platform_entity.unique_id,
            position=position,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class FanHelper:
    """Helper to issue fan commands."""

    def __init__(self, client: Client):
        """Initialize the fan helper."""
        self._client: Client = client

    async def turn_on(
        self,
        fan_platform_entity: BasePlatformEntity | GroupEntity,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
    ) -> CommandResponse:
        """Turn on a fan."""
        ensure_platform_entity(fan_platform_entity, Platform.FAN)
        command = FanTurnOnCommand(
            ieee=fan_platform_entity.device_ieee
            if not isinstance(fan_platform_entity, GroupEntity)
            else None,
            group_id=fan_platform_entity.group_id
            if isinstance(fan_platform_entity, GroupEntity)
            else None,
            unique_id=fan_platform_entity.unique_id,
            speed=speed,
            percentage=percentage,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(
        self,
        fan_platform_entity: BasePlatformEntity | GroupEntity,
    ) -> CommandResponse:
        """Turn off a fan."""
        ensure_platform_entity(fan_platform_entity, Platform.FAN)
        command = FanTurnOffCommand(
            ieee=fan_platform_entity.device_ieee
            if not isinstance(fan_platform_entity, GroupEntity)
            else None,
            group_id=fan_platform_entity.group_id
            if isinstance(fan_platform_entity, GroupEntity)
            else None,
            unique_id=fan_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_fan_percentage(
        self,
        fan_platform_entity: BasePlatformEntity | GroupEntity,
        percentage: int,
    ) -> CommandResponse:
        """Set a fan percentage."""
        ensure_platform_entity(fan_platform_entity, Platform.FAN)
        command = FanSetPercentageCommand(
            ieee=fan_platform_entity.device_ieee
            if not isinstance(fan_platform_entity, GroupEntity)
            else None,
            group_id=fan_platform_entity.group_id
            if isinstance(fan_platform_entity, GroupEntity)
            else None,
            unique_id=fan_platform_entity.unique_id,
            percentage=percentage,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_fan_preset_mode(
        self,
        fan_platform_entity: BasePlatformEntity | GroupEntity,
        preset_mode: str,
    ) -> CommandResponse:
        """Set a fan preset mode."""
        ensure_platform_entity(fan_platform_entity, Platform.FAN)
        command = FanSetPresetModeCommand(
            ieee=fan_platform_entity.device_ieee
            if not isinstance(fan_platform_entity, GroupEntity)
            else None,
            group_id=fan_platform_entity.group_id
            if isinstance(fan_platform_entity, GroupEntity)
            else None,
            unique_id=fan_platform_entity.unique_id,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class LockHelper:
    """Helper to issue lock commands."""

    def __init__(self, client: Client):
        """Initialize the lock helper."""
        self._client: Client = client

    async def lock(self, lock_platform_entity: BasePlatformEntity) -> CommandResponse:
        """Lock a lock."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockLockCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def unlock(self, lock_platform_entity: BasePlatformEntity) -> CommandResponse:
        """Unlock a lock."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockUnlockCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_user_lock_code(
        self,
        lock_platform_entity: BasePlatformEntity,
        code_slot: int,
        user_code: str,
    ) -> CommandResponse:
        """Set a user lock code."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockSetUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
            user_code=user_code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def clear_user_lock_code(
        self,
        lock_platform_entity: BasePlatformEntity,
        code_slot: int,
    ) -> CommandResponse:
        """Clear a user lock code."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockClearUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def enable_user_lock_code(
        self,
        lock_platform_entity: BasePlatformEntity,
        code_slot: int,
    ) -> CommandResponse:
        """Enable a user lock code."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockEnableUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def disable_user_lock_code(
        self,
        lock_platform_entity: BasePlatformEntity,
        code_slot: int,
    ) -> CommandResponse:
        """Disable a user lock code."""
        ensure_platform_entity(lock_platform_entity, Platform.LOCK)
        command = LockDisableUserLockCodeCommand(
            ieee=lock_platform_entity.device_ieee,
            unique_id=lock_platform_entity.unique_id,
            code_slot=code_slot,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class NumberHelper:
    """Helper to issue number commands."""

    def __init__(self, client: Client):
        """Initialize the number helper."""
        self._client: Client = client

    async def set_value(
        self,
        number_platform_entity: BasePlatformEntity,
        value: Union[int, float],
    ) -> CommandResponse:
        """Set a number."""
        ensure_platform_entity(number_platform_entity, Platform.NUMBER)
        command = NumberSetValueCommand(
            ieee=number_platform_entity.device_ieee,
            unique_id=number_platform_entity.unique_id,
            value=value,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SelectHelper:
    """Helper to issue select commands."""

    def __init__(self, client: Client):
        """Initialize the select helper."""
        self._client: Client = client

    async def select_option(
        self,
        select_platform_entity: BasePlatformEntity,
        option: Union[str, int],
    ) -> CommandResponse:
        """Set a select."""
        ensure_platform_entity(select_platform_entity, Platform.SELECT)
        command = SelectSelectOptionCommand(
            ieee=select_platform_entity.device_ieee,
            unique_id=select_platform_entity.unique_id,
            option=option,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class ClimateHelper:
    """Helper to issue climate commands."""

    def __init__(self, client: Client):
        """Initialize the climate helper."""
        self._client: Client = client

    async def set_hvac_mode(
        self,
        climate_platform_entity: BasePlatformEntity,
        hvac_mode: Literal[
            "heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"
        ],
    ) -> CommandResponse:
        """Set a climate."""
        ensure_platform_entity(climate_platform_entity, Platform.CLIMATE)
        command = ClimateSetHvacModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            hvac_mode=hvac_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_temperature(
        self,
        climate_platform_entity: BasePlatformEntity,
        hvac_mode: Optional[
            Literal["heat_cool", "heat", "cool", "auto", "dry", "fan_only", "off"]
        ] = None,
        temperature: Optional[float] = None,
        target_temp_high: Optional[float] = None,
        target_temp_low: Optional[float] = None,
    ) -> CommandResponse:
        """Set a climate."""
        ensure_platform_entity(climate_platform_entity, Platform.CLIMATE)
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
        climate_platform_entity: BasePlatformEntity,
        fan_mode: str,
    ) -> CommandResponse:
        """Set a climate."""
        ensure_platform_entity(climate_platform_entity, Platform.CLIMATE)
        command = ClimateSetFanModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            fan_mode=fan_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def set_preset_mode(
        self,
        climate_platform_entity: BasePlatformEntity,
        preset_mode: str,
    ) -> CommandResponse:
        """Set a climate."""
        ensure_platform_entity(climate_platform_entity, Platform.CLIMATE)
        command = ClimateSetPresetModeCommand(
            ieee=climate_platform_entity.device_ieee,
            unique_id=climate_platform_entity.unique_id,
            preset_mode=preset_mode,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class AlarmControlPanelHelper:
    """Helper to issue alarm control panel commands."""

    def __init__(self, client: Client):
        """Initialize the alarm control panel helper."""
        self._client: Client = client

    async def disarm(
        self, alarm_control_panel_platform_entity: BasePlatformEntity, code: str
    ) -> CommandResponse:
        """Disarm an alarm control panel."""
        ensure_platform_entity(
            alarm_control_panel_platform_entity, Platform.ALARM_CONTROL_PANEL
        )
        command = AlarmControlPanelDisarmCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_home(
        self, alarm_control_panel_platform_entity: BasePlatformEntity, code: str
    ) -> CommandResponse:
        """Arm an alarm control panel in home mode."""
        ensure_platform_entity(
            alarm_control_panel_platform_entity, Platform.ALARM_CONTROL_PANEL
        )
        command = AlarmControlPanelArmHomeCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_away(
        self, alarm_control_panel_platform_entity: BasePlatformEntity, code: str
    ) -> CommandResponse:
        """Arm an alarm control panel in away mode."""
        ensure_platform_entity(
            alarm_control_panel_platform_entity, Platform.ALARM_CONTROL_PANEL
        )
        command = AlarmControlPanelArmAwayCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def arm_night(
        self, alarm_control_panel_platform_entity: BasePlatformEntity, code: str
    ) -> CommandResponse:
        """Arm an alarm control panel in night mode."""
        ensure_platform_entity(
            alarm_control_panel_platform_entity, Platform.ALARM_CONTROL_PANEL
        )
        command = AlarmControlPanelArmNightCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
            code=code,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def trigger(
        self,
        alarm_control_panel_platform_entity: BasePlatformEntity,
    ) -> CommandResponse:
        """Trigger an alarm control panel alarm."""
        ensure_platform_entity(
            alarm_control_panel_platform_entity, Platform.ALARM_CONTROL_PANEL
        )
        command = AlarmControlPanelTriggerCommand(
            ieee=alarm_control_panel_platform_entity.device_ieee,
            unique_id=alarm_control_panel_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class PlatformEntityHelper:
    """Helper to send global platform entity commands."""

    def __init__(self, client: Client):
        """Initialize the platform entity helper."""
        self._client: Client = client

    async def refresh_state(
        self, platform_entity: BasePlatformEntity
    ) -> CommandResponse:
        """Refresh the state of a platform entity."""
        command = PlatformEntityRefreshStateCommand(
            ieee=platform_entity.device_ieee,
            unique_id=platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class ClientHelper:
    """Helper to send client specific commands."""

    def __init__(self, client: Client):
        """Initialize the client helper."""
        self._client: Client = client

    async def listen(self) -> CommandResponse:
        """Listen for incoming messages."""
        command = ClientListenCommand()
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def listen_raw_zcl(self) -> CommandResponse:
        """Listen for incoming raw ZCL messages."""
        command = ClientListenRawZCLCommand()
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def disconnect(self) -> CommandResponse:
        """Disconnect this client from the server."""
        command = ClientDisconnectCommand()
        return await self._client.async_send_command(command.dict(exclude_none=True))


class GroupHelper:
    """Helper to send group commands."""

    def __init__(self, client: Client):
        """Initialize the group helper."""
        self._client: Client = client

    async def get_groups(self) -> dict[int, Group]:
        """Get the groups."""
        response = cast(
            GroupsResponse,
            await self._client.async_send_command(
                GetGroupsCommand().dict(exclude_none=True)
            ),
        )
        return response.groups

    async def create_group(
        self,
        name: str,
        unique_id: Optional[int] = None,
        members: Optional[list[BasePlatformEntity]] = None,
    ) -> Group:
        """Create a new group."""
        request_data: dict[str, Any] = {
            "group_name": name,
            "group_id": unique_id,
        }
        if members is not None:
            request_data["members"] = [
                {"ieee": member.device_ieee, "endpoint_id": member.endpoint_id}
                for member in members
            ]

        command = CreateGroupCommand(**request_data)
        response = cast(
            UpdateGroupResponse,
            await self._client.async_send_command(command.dict(exclude_none=True)),
        )
        return response.group

    async def remove_groups(self, groups: list[Group]) -> dict[int, Group]:
        """Remove groups."""
        request: dict[str, Any] = {
            "group_ids": [group.id for group in groups],
        }
        command = RemoveGroupsCommand(**request)
        response = cast(
            GroupsResponse,
            await self._client.async_send_command(command.dict(exclude_none=True)),
        )
        return response.groups

    async def add_group_members(
        self, group: Group, members: list[BasePlatformEntity]
    ) -> Group:
        """Add members to a group."""
        request_data: dict[str, Any] = {
            "group_id": group.id,
            "members": [
                {"ieee": member.device_ieee, "endpoint_id": member.endpoint_id}
                for member in members
            ],
        }

        command = AddGroupMembersCommand(**request_data)
        response = cast(
            UpdateGroupResponse,
            await self._client.async_send_command(command.dict(exclude_none=True)),
        )
        return response.group

    async def remove_group_members(
        self, group: Group, members: list[BasePlatformEntity]
    ) -> Group:
        """Remove members from a group."""
        request_data: dict[str, Any] = {
            "group_id": group.id,
            "members": [
                {"ieee": member.device_ieee, "endpoint_id": member.endpoint_id}
                for member in members
            ],
        }

        command = RemoveGroupMembersCommand(**request_data)
        response = cast(
            UpdateGroupResponse,
            await self._client.async_send_command(command.dict(exclude_none=True)),
        )
        return response.group


class DeviceHelper:
    """Helper to send device commands."""

    def __init__(self, client: Client):
        """Initialize the device helper."""
        self._client: Client = client

    async def get_devices(self) -> dict[str, Device]:
        """Get the groups."""
        response = cast(
            GetDevicesResponse,
            await self._client.async_send_command(
                GetDevicesCommand().dict(exclude_none=True)
            ),
        )
        return response.devices

    async def reconfigure_device(self, device: Device) -> None:
        """Reconfigure a device."""
        await self._client.async_send_command(
            ReconfigureDeviceCommand(ieee=device.ieee).dict(exclude_none=True)
        )

    async def read_cluster_attributes(
        self,
        device: Device,
        cluster_id: int,
        cluster_type: str,
        endpoint_id: int,
        attributes: list[str],
        manufacturer_code: Optional[int] = None,
    ) -> ReadClusterAttributesResponse:
        """Read cluster attributes."""
        response = cast(
            ReadClusterAttributesResponse,
            await self._client.async_send_command(
                ReadClusterAttributesCommand(
                    ieee=device.ieee,
                    endpoint_id=endpoint_id,
                    cluster_id=cluster_id,
                    cluster_type=cluster_type,
                    attributes=attributes,
                    manufacturer_code=manufacturer_code,
                ).dict(exclude_none=True)
            ),
        )
        return response

    async def write_cluster_attribute(
        self,
        device: Device,
        cluster_id: int,
        cluster_type: str,
        endpoint_id: int,
        attribute: str,
        value: Any,
        manufacturer_code: Optional[int] = None,
    ) -> WriteClusterAttributeResponse:
        """Set the value for a cluster attribute."""
        response = cast(
            WriteClusterAttributeResponse,
            await self._client.async_send_command(
                WriteClusterAttributeCommand(
                    ieee=device.ieee,
                    endpoint_id=endpoint_id,
                    cluster_id=cluster_id,
                    cluster_type=cluster_type,
                    attribute=attribute,
                    value=value,
                    manufacturer_code=manufacturer_code,
                ).dict(exclude_none=True)
            ),
        )
        return response


class NetworkHelper:
    """Helper for network commands."""

    def __init__(self, client: Client):
        """Initialize the device helper."""
        self._client: Client = client

    async def permit_joining(
        self, duration: int = 255, device: Optional[Device] = None
    ) -> bool:
        """Permit joining for a specified duration."""
        # TODO add permit with code support
        request_data: dict[str, Any] = {
            "duration": duration,
        }
        if device is not None:
            if device.device_type == "EndDevice":
                raise ValueError("Device is not a coordinator or router")
            request_data["ieee"] = device.ieee
        command = PermitJoiningCommand(**request_data)
        response = cast(
            PermitJoiningResponse,
            await self._client.async_send_command(command.dict(exclude_none=True)),
        )
        return response.success

    async def update_topology(self) -> None:
        """Update the network topology."""
        await self._client.async_send_command(
            UpdateNetworkTopologyCommand().dict(exclude_none=True)
        )

    async def start_network(self, configuration: dict) -> bool:
        """Start the Zigbee network."""
        command = StartNetworkCommand(
            **configuration
        )  # TODO do this correctly once fully modeled
        response = await self._client.async_send_command(
            command.dict(exclude_none=True)
        )
        return response.success

    async def stop_network(self) -> bool:
        """Stop the Zigbee network."""
        response = await self._client.async_send_command(
            StopNetworkCommand().dict(exclude_none=True)
        )
        return response.success


class ServerHelper:
    """Helper for server commands."""

    def __init__(self, client: Client):
        """Initialize the helper."""
        self._client: Client = client

    async def stop_server(self) -> bool:
        """Stop the websocket server."""
        response = await self._client.async_send_command(
            StopServerCommand().dict(exclude_none=True)
        )
        return response.success
