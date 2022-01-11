"""Event models for zhawss.

Events are unprompted messages from the server -> client and they contain only the data that is necessary to handle the event.
"""

from typing import Annotated, Any, Literal, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.types import BaseDevice, Device, DeviceSignature


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


class BaseEvent(BaseModel):
    """Base event model."""

    message_type: Literal["event"] = "event"


class PlatformEntityEvent(BaseEvent):
    """Platform entity event."""

    """TODO use this as a base and create specific events for each entity type where state and attributes is fully modeled out"""
    event_type: Literal["platform_entity_event"]
    event: Literal["platform_entity_state_changed"]
    platform_entity: MinimalPlatformEntity
    endpoint: MinimalEndpoint
    device: MinimalDevice
    state: Any


class ZCLAttributeUpdatedEvent(BaseEvent):
    """ZCL attribute updated event."""

    event_type: Literal["raw_zcl"]
    event: Literal["attribute_updated"]
    device: MinimalDevice
    cluster_handler: MinimalClusterHandler
    attribute: Attribute
    endpoint: MinimalEndpoint


class ControllerEvent(BaseEvent):
    """Controller event."""

    event_type: Literal["controller_event"]


class DeviceJoinedEvent(ControllerEvent):
    """Device joined event."""

    event: Literal["device_joined"]
    ieee: str
    nwk: str
    pairing_status: str


class RawDeviceInitializedEvent(ControllerEvent):
    """Raw device initialized event."""

    event: Literal["raw_device_initialized"]
    ieee: str
    nwk: str
    pairing_status: str
    manufacturer: str
    model: str
    signature: DeviceSignature


class DeviceFullyInitializedEvent(ControllerEvent):
    """Device fully initialized event."""

    event: Literal["device_fully_initialized"]
    ieee: str
    nwk: str
    pairing_status: str
    manufacturer: str
    model: str
    device: Device


class DeviceConfiguredEvent(ControllerEvent):
    """Device configured event."""

    event: Literal["device_configured"]
    ieee: str
    nwk: str
    pairing_status: str
    manufacturer: str
    model: str
    device: BaseDevice


class DeviceLeftEvent(ControllerEvent):
    """Device left event."""

    event: Literal["device_left"]
    ieee: str
    nwk: str


class DeviceRemovedEvent(ControllerEvent):
    """Device removed event."""

    event: Literal["device_removed"]
    device: Device


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
    ],
    Field(discriminator="event"),  # noqa: F821
]
