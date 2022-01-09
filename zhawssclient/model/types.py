"""Models that represent types for the zhawssclient."""


from typing import Any, Dict, List, Union

from zigpy.types.named import EUI64

from zhawssclient.event import EventBase
from zhawssclient.model import BaseModel


class BaseEventedModel(BaseModel, EventBase):
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
    device_ieee: EUI64
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


class Device(BaseEventedModel):
    """Device model."""

    ieee: EUI64
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
    entities: Dict[str, BasePlatformEntity]
    neighbors: List[Any]
