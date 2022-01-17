"""Models that represent types for the zhaws.client.

Types are representations of the objects that exist in zhawss.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic.fields import Field

from zhaws.client.event import EventBase
from zhaws.client.model import BaseModel


class BaseEventedModel(EventBase, BaseModel):
    """Base evented model."""


class Cluster(BaseModel):
    """Cluster model."""

    id: int
    endpoint_attribute: str
    name: str
    endpoint_id: int
    type: str
    commands: list[str]


class ClusterHandler(BaseModel):
    """Cluster handler model."""

    unique_id: str
    cluster: Cluster
    class_name: str
    generic_id: str
    endpoint_id: int
    id: str
    status: str


class Endpoint(BaseModel):
    """Endpoint model."""

    id: int


class DeviceTrackerState(BaseModel):
    """Device tracker state model."""

    connected: bool
    battery_level: Optional[float]


class CoverState(BaseModel):
    """Cover state model."""

    current_position: int
    state: Optional[str]
    is_opening: bool
    is_closing: bool
    is_closed: bool


class ShadeState(BaseModel):
    """Cover state model."""

    current_position: int
    is_closed: bool


class FanState(BaseModel):
    """Fan state model."""

    preset_mode: str
    percentage: int


class LockState(BaseModel):
    """Lock state model."""

    is_locked: bool


class BatteryState(BaseModel):
    """Battery state model."""

    state: Optional[Union[str, float, int]]
    battery_size: Optional[str]
    battery_quantity: Optional[str]
    battery_voltage: Optional[float]


class ElectricalMeasurementState(BaseModel):
    """Electrical measurement state model."""

    state: Optional[Union[str, float, int]]
    measurement_type: Optional[str]


class LightState(BaseModel):
    """Light state model."""

    on: bool
    brightness: Optional[int]
    hs_color: Optional[tuple[float, float]]
    color_temp: Optional[int]
    effect: Optional[str]
    off_brightness: Optional[int]


class SwitchState(BaseModel):
    """Switch state model."""

    state: bool


class SmareEnergyMeteringState(BaseModel):
    """Smare energy metering state model."""

    state: Optional[Union[str, float, int]]
    device_type: Optional[str]
    status: Optional[str]


class BasePlatformEntity(BaseEventedModel):
    """Base platform entity model."""

    name: str
    unique_id: str
    platform: str
    device_ieee: str
    endpoint_id: int
    class_name: str


class LockEntity(BasePlatformEntity):
    """Lock entity model."""

    class_name: Literal["Lock"]
    state: LockState


class DeviceTrackerEntity(BasePlatformEntity):
    """Device tracker entity model."""

    class_name: Literal["DeviceTracker"]
    state: DeviceTrackerState


class CoverEntity(BasePlatformEntity):
    """Cover entity model."""

    class_name: Literal["Cover"]
    state: CoverState


class ShadeEntity(BasePlatformEntity):
    """Shade entity model."""

    class_name: Literal["Shade", "KeenVent"]
    state: ShadeState


class BinarySensorEntity(BasePlatformEntity):
    """Binary sensor model."""

    class_name: Literal[
        "Accelerometer", "Occupancy", "Opening", "BinaryInput", "Motion", "IASZone"
    ]
    sensor_attribute: str
    state: bool


class BaseSensorEntity(BasePlatformEntity):
    """Sensor model."""

    attribute: Optional[str]
    decimals: int
    divisor: int
    multiplier: Union[int, float]
    unit: Optional[str]


class SensorEntity(BaseSensorEntity):
    """Sensor entity model."""

    class_name: Literal[
        "AnalogInput",
        "Humidity",
        "SoilMoisture",
        "LeafWetness",
        "Illuminance",
        "Pressure",
        "Temperature",
        "CarbonDioxideConcentration",
        "CarbonMonoxideConcentration",
        "VOCLevel",
        "PPBVOCLevel",
        "FormaldehydeConcentration",
        "ThermostatHVACAction",
        "SinopeHVACAction",
        "RSSISensor",
        "LQISensor",
    ]
    state: Optional[Union[str, float, int]]


class BatteryEntity(BaseSensorEntity):
    """Battery entity model."""

    class_name: Literal["Battery"]
    state: BatteryState


class ElectricalMeasurementEntity(BaseSensorEntity):
    """Electrical measurement entity model."""

    class_name: Literal[
        "ElectricalMeasurement",
        "ElectricalMeasurementApparentPower",
        "ElectricalMeasurementRMSCurrent",
        "ElectricalMeasurementRMSVoltage",
    ]
    state: ElectricalMeasurementState


class SmareEnergyMeteringEntity(BaseSensorEntity):
    """Smare energy metering entity model."""

    class_name: Literal["SmartEnergyMetering", "SmartEnergySummation"]
    state: SmareEnergyMeteringState


class AlarmControlPanelEntity(BasePlatformEntity):
    """Alarm control panel model."""

    class_name: Literal["ZHAAlarmControlPanel"]
    supported_features: int
    code_required_arm_actions: bool
    max_invalid_tries: int
    state: str


class ButtonEntity(BasePlatformEntity):
    """Button model."""

    class_name: Literal["IdentifyButton"]
    command: str


class FanEntity(BasePlatformEntity):
    """Fan model."""

    class_name: Literal["Fan"]
    preset_modes: list[str]
    supported_features: int
    speed_count: int
    state: FanState


class LightEntity(BasePlatformEntity):
    """Light model."""

    class_name: Literal["Light", "HueLight", "ForceOnLight"]
    supported_features: int
    min_mireds: int
    max_mireds: int
    effect_list: Optional[list[str]]
    state: LightState


class NumberEntity(BasePlatformEntity):
    """Number entity model."""

    class_name: Literal["Number"]
    engineer_units: int
    application_type: int
    step: float
    min_value: float
    max_value: float
    name: str
    state: float


class SelectEntity(BasePlatformEntity):
    """Select entity model."""

    class_name: Literal[
        "DefaultToneSelectEntity",
        "DefaultSirenLevelSelectEntity",
        "DefaultStrobeLevelSelectEntity",
        "DefaultStrobeSelectEntity",
    ]
    enum: str
    options: list[str]
    state: Optional[str]


class SirenEntity(BasePlatformEntity):
    """Siren entity model."""

    class_name: Literal["Siren"]
    available_tones: Optional[Union[list[Union[int, str]], dict[int, str]]]
    supported_features: int
    state: bool


class SwitchEntity(BasePlatformEntity):
    """Switch entity model."""

    class_name: Literal["Switch"]
    state: SwitchState


ENTITIES = Annotated[
    Union[
        SirenEntity,
        SelectEntity,
        NumberEntity,
        LightEntity,
        FanEntity,
        ButtonEntity,
        AlarmControlPanelEntity,
        SensorEntity,
        BinarySensorEntity,
        DeviceTrackerEntity,
        ShadeEntity,
        CoverEntity,
        LockEntity,
        SwitchEntity,
        BatteryEntity,
        ElectricalMeasurementEntity,
        SmareEnergyMeteringEntity,
    ],
    Field(discriminator="class_name"),  # noqa: F821
]


class DeviceSignatureEndpoint(BaseModel):
    """Device signature endpoint model."""

    profile_id: Optional[str]
    device_type: Optional[str]
    input_clusters: list[str]
    output_clusters: list[str]


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
    endpoints: dict[int, DeviceSignatureEndpoint]


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

    entities: dict[str, ENTITIES]
    neighbors: list[Any]
