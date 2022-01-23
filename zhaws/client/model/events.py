"""Event models for zhawss.

Events are unprompted messages from the server -> client and they contain only the data that is necessary to handle the event.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic.fields import Field

from zhaws.client.model.types import (
    BaseDevice,
    BatteryState,
    BooleanState,
    CoverState,
    Device,
    DeviceSignature,
    DeviceTrackerState,
    ElectricalMeasurementState,
    FanState,
    GenericState,
    Group,
    LightState,
    LockState,
    ShadeState,
    SmareEnergyMeteringState,
    SwitchState,
)
from zhaws.model import BaseEvent, BaseModel


class MinimalPlatformEntity(BaseModel):
    """Platform entity model."""

    name: str
    unique_id: str
    platform: str


class MinimalEndpoint(BaseModel):
    """Minimal endpoint model."""

    id: int


class MinimalDevice(BaseModel):
    """Minimal device model."""

    ieee: str


class Attribute(BaseModel):
    """Attribute model."""

    id: int
    name: str
    value: Any


class MinimalCluster(BaseModel):
    """Minimal cluster model."""

    id: int
    endpoint_attribute: str
    name: str
    endpoint_id: int


class MinimalClusterHandler(BaseModel):
    """Minimal cluster handler model."""

    unique_id: str
    cluster: MinimalCluster


class MinimalGroup(BaseModel):
    """Minimal group model."""

    id: int


class PlatformEntityEvent(BaseEvent):
    """Platform entity event."""

    """TODO use this as a base and create specific events for each entity type where state and attributes is fully modeled out"""
    event_type: Literal["platform_entity_event"] = "platform_entity_event"
    event: Literal["platform_entity_state_changed"] = "platform_entity_state_changed"
    platform_entity: MinimalPlatformEntity
    endpoint: Optional[MinimalEndpoint]
    device: Optional[MinimalDevice]
    group: Optional[MinimalGroup]
    state: Annotated[
        Union[
            DeviceTrackerState,
            CoverState,
            ShadeState,
            FanState,
            LockState,
            BatteryState,
            ElectricalMeasurementState,
            LightState,
            SwitchState,
            SmareEnergyMeteringState,
            GenericState,
            BooleanState,
        ],
        Field(discriminator="class_name"),  # noqa: F821
    ]


class ZCLAttributeUpdatedEvent(BaseEvent):
    """ZCL attribute updated event."""

    event_type: Literal["raw_zcl_event"] = "raw_zcl_event"
    event: Literal["attribute_updated"] = "attribute_updated"
    device: MinimalDevice
    cluster_handler: MinimalClusterHandler
    attribute: Attribute
    endpoint: MinimalEndpoint


class ControllerEvent(BaseEvent):
    """Controller event."""

    event_type: Literal["controller_event"] = "controller_event"


class DevicePairingEvent(ControllerEvent):
    """Device pairing event."""

    pairing_status: str


class DeviceJoinedEvent(DevicePairingEvent):
    """Device joined event."""

    event: Literal["device_joined"] = "device_joined"
    ieee: str
    nwk: str


class RawDeviceInitializedEvent(DevicePairingEvent):
    """Raw device initialized event."""

    event: Literal["raw_device_initialized"] = "raw_device_initialized"
    ieee: str
    nwk: str
    manufacturer: str
    model: str
    signature: DeviceSignature


class DeviceFullyInitializedEvent(DevicePairingEvent):
    """Device fully initialized event."""

    event: Literal["device_fully_initialized"] = "device_fully_initialized"
    device: Device


class DeviceConfiguredEvent(DevicePairingEvent):
    """Device configured event."""

    event: Literal["device_configured"] = "device_configured"
    device: BaseDevice


class DeviceLeftEvent(ControllerEvent):
    """Device left event."""

    event: Literal["device_left"] = "device_left"
    ieee: str
    nwk: str


class DeviceRemovedEvent(ControllerEvent):
    """Device removed event."""

    event: Literal["device_removed"] = "device_removed"
    device: Device


class DeviceOfflineEvent(BaseEvent):
    """Device offline event."""

    event: Literal["device_offline"] = "device_offline"
    event_type: Literal["device_event"] = "device_event"
    device: MinimalDevice


class DeviceOnlineEvent(BaseEvent):
    """Device online event."""

    event: Literal["device_online"] = "device_online"
    event_type: Literal["device_event"] = "device_event"
    device: MinimalDevice


class GroupRemovedEvent(ControllerEvent):
    """Group removed event."""

    event: Literal["group_removed"] = "group_removed"
    group: Group


class GroupAddedEvent(ControllerEvent):
    """Group added event."""

    event: Literal["group_added"] = "group_added"
    group: Group


class GroupMemberAddedEvent(ControllerEvent):
    """Group member added event."""

    event: Literal["group_member_added"] = "group_member_added"
    group: Group


class GroupMemberRemovedEvent(ControllerEvent):
    """Group member removed event."""

    event: Literal["group_member_removed"] = "group_member_removed"
    group: Group


Events = Annotated[
    Union[
        PlatformEntityEvent,
        ZCLAttributeUpdatedEvent,
        DeviceJoinedEvent,
        RawDeviceInitializedEvent,
        DeviceFullyInitializedEvent,
        DeviceConfiguredEvent,
        DeviceLeftEvent,
        DeviceRemovedEvent,
        GroupRemovedEvent,
        GroupAddedEvent,
        GroupMemberAddedEvent,
        GroupMemberRemovedEvent,
        DeviceOfflineEvent,
        DeviceOnlineEvent,
    ],
    Field(discriminator="event"),  # noqa: F821
]
