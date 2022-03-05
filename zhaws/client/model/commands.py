"""Models that represent commands and command responses."""

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import validator
from pydantic.fields import Field
from zigpy.types.named import EUI64

from zhaws.client.model.events import MinimalCluster, MinimalDevice
from zhaws.client.model.types import Device, Group
from zhaws.model import BaseModel


class CommandResponse(BaseModel):
    """Command response model."""

    message_type: Literal["result"] = "result"
    message_id: int
    success: bool


class DefaultResponse(CommandResponse):
    """Default command response."""

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
        "number_set_value",
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
    devices: dict[EUI64, Device]

    @validator("devices", pre=True, always=True, each_item=False, check_fields=False)
    def convert_device_ieee(
        cls, devices: dict[str, dict], values: dict[str, Any], **kwargs: Any
    ) -> dict[EUI64, Device]:
        return {EUI64.convert(k): Device(**v) for k, v in devices.items()}


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

    command: Literal["get_groups", "create_group", "remove_groups"]
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
