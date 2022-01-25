"""Models that represent commands and command responses."""

from typing import Annotated, Any, Literal, Optional, Tuple, Type, Union

from pydantic import conint
from pydantic.fields import Field

from zhaws.client.model.events import MinimalCluster, MinimalDevice
from zhaws.client.model.types import Device, Group, GroupMemberReference
from zhaws.model import BaseModel


class Command(BaseModel):
    """Base class for command that are sent to the server."""

    command: str


class PermitJoiningCommand(Command):
    """Command to permit joining."""

    command: Literal["permit_joining"] = "permit_joining"
    duration: Type[int] = conint(ge=1, le=254)
    device: Optional[Device]


class StopNetworkCommand(Command):
    """Command to stop the zigbee network."""

    command: Literal["stop_network"] = "stop_network"


class ZigbeeCoordinatorDeviceConfiguration(BaseModel):
    """Configuration of the zigbee coordinator."""

    path: str
    flow_control: str
    baudrate: int


class StartNetworkCommand(Command):
    """Command to start the zigbee network."""

    # TODO model this out correctly
    command: Literal["start_network"] = "start_network"
    radio_type: str
    device: ZigbeeCoordinatorDeviceConfiguration
    database_path: str
    enable_quirks: bool


class StopServerCommand(Command):
    """Command to stop the websocket server."""

    command: Literal["stop_server"] = "stop_server"


class UpdateNetworkTopologyCommand(Command):
    """Command to update the network topology."""

    command: Literal["update_network_topology"] = "update_network_topology"


class GetDevicesCommand(Command):
    """Command to get devices."""

    command: Literal["get_devices"] = "get_devices"


class ReconfigureDeviceCommand(Command):
    """Command to reconfigure a device."""

    command: Literal["reconfigure_device"] = "reconfigure_device"
    ieee: str


class ReadClusterAttributesCommand(Command):
    """Command to get the values of the specified attributes."""

    command: Literal["read_cluster_attributes"] = "read_cluster_attributes"
    ieee: str
    endpoint_id: int
    cluster_id: int
    cluster_type: Literal["in", "out"]
    attributes: list[str]
    manufacturer_code: Optional[int]


class WriteClusterAttributeCommand(Command):
    """Command to set the value for a cluster attribute."""

    command: Literal["write_cluster_attribute"] = "write_cluster_attribute"
    ieee: str
    endpoint_id: int
    cluster_id: int
    cluster_type: Literal["in", "out"]
    attribute: str
    value: Any
    manufacturer_code: Optional[int]


class GetGroupsCommand(Command):
    """Command to get groups."""

    command: Literal["get_groups"] = "get_groups"


class CreateGroupCommand(Command):
    """Command to create a group."""

    command: Literal["create_group"] = "create_group"
    group_name: str
    group_id: Optional[int]
    members: Optional[list[GroupMemberReference]]


class RemoveGroupsCommand(Command):
    """Command to remove groups."""

    command: Literal["remove_groups"] = "remove_groups"
    group_ids: list[int]


class AddGroupMembersCommand(Command):
    """Command to add members to a group."""

    command: Literal["add_group_members"] = "add_group_members"
    group_id: int
    members: list[GroupMemberReference]


class RemoveGroupMembersCommand(Command):
    """Command to remove members from a group."""

    command: Literal["remove_group_members"] = "remove_group_members"
    group_id: int
    members: list[GroupMemberReference]


class PlatformEntityCommand(Command):
    """Base class for commands that address individual platform entities."""

    unique_id: str
    group_id: Optional[int]
    ieee: Optional[str]


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
    percentage: Optional[conint(ge=0, le=100)]  # type: ignore #TODO see if there is a way to make this work mypy
    preset_mode: Optional[str]


class FanTurnOffCommand(PlatformEntityCommand):
    """Command to turn off a fan platform entity."""

    command: Literal["fan_turn_off"] = "fan_turn_off"


class FanSetPercentageCommand(PlatformEntityCommand):
    """Command to set the speed percentage for a fan platform entity."""

    command: Literal["fan_set_percentage"] = "fan_set_percentage"
    percentage: Optional[conint(ge=0, le=100)]  # type: ignore #TODO see if there is a way to make this work mypy


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
    code: Optional[str]


class AlarmControlPanelArmHomeCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in home mode."""

    command: Literal["alarm_control_panel_arm_home"] = "alarm_control_panel_arm_home"
    code: Optional[str]


class AlarmControlPanelArmAwayCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in away mode."""

    command: Literal["alarm_control_panel_arm_away"] = "alarm_control_panel_arm_away"
    code: Optional[str]


class AlarmControlPanelArmNightCommand(PlatformEntityCommand):
    """Command to arm an alarm control panel platform entity in night mode."""

    command: Literal["alarm_control_panel_arm_night"] = "alarm_control_panel_arm_night"
    code: Optional[str]


class AlarmControlPanelTriggerCommand(PlatformEntityCommand):
    """Command to trigger the alarm for an alarm control panel platform entity."""

    command: Literal["alarm_control_panel_trigger"] = "alarm_control_panel_trigger"
    code: Optional[str]


class PlatformEntityRefreshStateCommand(PlatformEntityCommand):
    """Command to refresh the state of a platform entity."""

    command: Literal["platform_entity_refresh_state"] = "platform_entity_refresh_state"


class ClientListenCommand(Command):
    """Command to listen to events for a client."""

    command: Literal["client_listen"] = "client_listen"


class ClientListenRawZCLCommand(Command):
    """Command to listen to raw zcl events for a client."""

    command: Literal["client_listen_raw_zcl"] = "client_listen_raw_zcl"


class ClientDisconnectCommand(Command):
    """Command to disconnect a client."""

    command: Literal["client_disconnect"] = "client_disconnect"


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
        "platform_entity_refresh_state",
        "client_listen",
        "client_listen_raw_zcl",
        "client_disconnect",
        "reconfigure_device",
        "UpdateNetworkTopologyCommand",
    ]


class PermitJoiningResponse(CommandResponse):
    """Get devices response."""

    command: Literal["permit_joining"] = "permit_joining"
    duration: int


class GetDevicesResponse(CommandResponse):
    """Get devices response."""

    command: Literal["get_devices"] = "get_devices"
    devices: dict[str, Device]


class ReadClusterAttributesResponse(CommandResponse):
    """Read cluster attributes response."""

    command: Literal["read_cluster_attributes"] = "read_cluster_attributes"
    device: MinimalDevice
    cluster: MinimalCluster
    manufacturer_code: Optional[int]
    succeeded: dict[str, Any]
    failed: dict[str, Any]


class AttributeStatus(BaseModel):
    """Attribute status."""

    attribute: str
    status: str


class WriteClusterAttributeResponse(CommandResponse):
    """Write cluster attribute response."""

    command: Literal["write_cluster_attribute"] = "write_cluster_attribute"
    device: MinimalDevice
    cluster: MinimalCluster
    manufacturer_code: Optional[int]
    response: AttributeStatus


class GroupsResponse(CommandResponse):
    """Get groups response."""

    command: Literal["get_groups", "create_group"]
    groups: dict[int, Group]


class UpdateGroupResponse(CommandResponse):
    """Update group response."""

    command: Literal["create_group", "add_group_members", "remove_group_members"]
    group: Group


CommandResponses = Annotated[
    Union[
        DefaultResponse,
        GetDevicesResponse,
        GroupsResponse,
        PermitJoiningResponse,
        UpdateGroupResponse,
        ReadClusterAttributesResponse,
        WriteClusterAttributeResponse,
    ],
    Field(discriminator="command"),  # noqa: F821
]
