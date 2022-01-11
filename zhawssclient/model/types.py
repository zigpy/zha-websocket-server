"""Models that represent types for the zhawssclient.

Types are representations of the objects that exist in zhawss.
"""


from typing import TYPE_CHECKING, Any, Dict, List, Union

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

    profile_id: int
    device_type: str
    in_clusters: List[str]
    out_clusters: List[str]


class DeviceSignature(BaseModel):
    node_descriptor: str
    endpoints: Dict[int, DeviceSignatureEndpoint]


class BaseDevice(BaseModel):
    """Base device model."""

    ieee: str
    nwk: int
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
