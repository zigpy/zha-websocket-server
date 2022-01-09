"""Event models for zhawss."""

from typing import Annotated, Any, Literal, Union

from pydantic.fields import Field
from zigpy.types.named import EUI64

from zhawssclient.model import BaseModel
from zhawssclient.model.messages import BaseMessage


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

    ieee: EUI64


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


class PlatformEntityEvent(BaseModel):
    """Platform entity event."""

    event_type: Literal["platform_entity_event"]
    event: Literal["platform_entity_state_changed"]
    platform_entity: MinimalPlatformEntity
    endpoint: MinimalEndpoint
    device: MinimalDevice
    state: Any


class ZCLAttributeUpdatedEvent(BaseModel):
    """ZCL attribute updated event."""

    event_type: Literal["raw_zcl"]
    event: Literal["attribute_updated"]
    device: MinimalDevice
    cluster_handler: MinimalClusterHandler
    attribute: Attribute
    endpoint: MinimalEndpoint


class Event(BaseMessage):
    """Event class."""

    message_type: Literal["event"] = "event"
    data: Annotated[
        Union[PlatformEntityEvent, ZCLAttributeUpdatedEvent],
        Field(discriminator="event"),  # noqa: F821
    ] = None
