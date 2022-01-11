"""Models that represent types for the zhawssclient.

Types are representations of the objects that exist in zhawss.
"""


from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from zhawssclient.event import EventBase
from zhawssclient.model import BaseModel

ControllerType = "Controller"
ClientType = "Client"


if TYPE_CHECKING:
    from zhawssclient.client import Client
    from zhawssclient.controller import Controller

    ClientType = Client
    ControllerType = Controller


class BaseEventedModel(EventBase, BaseModel):
    """Base evented model."""


class Cluster(BaseModel):
    """Cluster model."""

    id: int
    endpoint_attribute: str
    name: str
    endpoint_id: int
    type: str
    commands: List[str]


class ClusterHandler(BaseModel):
    """Cluster handler model."""

    unique_id: str
    cluster: Cluster
    class_name: str
    generic_id: str
    endpoint_id: int
    cluster: Cluster
    id: str
    status: str


class Endpoint(BaseModel):
    """Endpoint model."""

    id: int


class BasePlatformEntity(BaseEventedModel):
    """Base platform entity model."""

    name: str
    unique_id: str
    platform: str
    device_ieee: str
    endpoint_id: int
    class_name: str


class DeviceSignatureEndpoint(BaseModel):
    """Device signature endpoint model."""

    profile_id: Optional[str]
    device_type: Optional[str]
    input_clusters: List[str]
    output_clusters: List[str]


class NodeDescriptor(BaseModel):
    """Node descriptor model."""

    logical_type: int
    complex_descriptor_available: bool
    user_descriptor_available: bool
    reserved: int
    aps_flags: int
    frequency_band: int
    mac_capability_flags: int
    manufacturer_code: int
    maximum_buffer_size: int
    maximum_incoming_transfer_size: int
    server_mask: int
    maximum_outgoing_transfer_size: int
    descriptor_capability_field: int


class DeviceSignature(BaseModel):
    node_descriptor: Optional[NodeDescriptor]
    manufacturer: Optional[str]
    model: Optional[str]
    endpoints: Dict[int, DeviceSignatureEndpoint]


class BaseDevice(BaseModel):
    """Base device model."""

    ieee: str
    nwk: str
    manufacturer: str
    model: str
    name: str
    quirk_applied: bool
    quirk_class: Union[str, None]
    manufacturer_code: int
    power_source: str
    lqi: Union[int, None]
    rssi: Union[int, None]
    last_seen: str
    available: bool
    device_type: str
    signature: DeviceSignature


class Device(BaseDevice):
    """Device model."""

    entities: Dict[str, BasePlatformEntity]
    neighbors: List[Any]
