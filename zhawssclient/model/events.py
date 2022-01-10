"""Event models for zhawss.

Events are unprompted messages from the server -> client and they contain only the data that is necessary to handle the event.
"""

from typing import Annotated, Any, Literal, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel


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


Events = Annotated[
    Union[PlatformEntityEvent, ZCLAttributeUpdatedEvent],
    Field(discriminator="event"),  # noqa: F821
]
