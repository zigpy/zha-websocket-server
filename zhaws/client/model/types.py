"""Models that represent types for the zhaws.client.

Types are representations of the objects that exist in zhawss.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic.fields import Field

from zhaws.event import EventBase
from zhaws.model import BaseModel


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
    unique_id: str


class GenericState(BaseModel):
    """Default state model."""

    class_name: Literal[
        "ZHAAlarmControlPanel",
        "Number",
        "DefaultToneSelectEntity",
        "DefaultSirenLevelSelectEntity",
        "DefaultStrobeLevelSelectEntity",
        "DefaultStrobeSelectEntity",
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
        "LastSeenSensor",
        # TODO following are temporary until we have a proper implementation
        "Thermostat",
        "SinopeTechnologiesThermostat",
        "ZenWithinThermostat",
        "MoesThermostat",
        "BecaThermostat",
    ]
    state: Union[str, bool, int, float, None]


class DeviceTrackerState(BaseModel):
    """Device tracker state model."""

    class_name: Literal["DeviceTracker"] = "DeviceTracker"
    connected: bool
    battery_level: Optional[float]


class BooleanState(BaseModel):
    """Boolean value state model."""

    class_name: Literal[
        "Accelerometer",
        "Occupancy",
        "Opening",
        "BinaryInput",
        "Motion",
        "IASZone",
        "Siren",
    ]
    state: bool


class CoverState(BaseModel):
    """Cover state model."""

    class_name: Literal["Cover"] = "Cover"
    current_position: int
    state: Optional[str]
    is_opening: bool
    is_closing: bool
    is_closed: bool


class ShadeState(BaseModel):
    """Cover state model."""

    class_name: Literal["Shade", "KeenVent"]
    current_position: Optional[
        int
    ]  # TODO: how should we represent this when it is None?
    is_closed: bool
    state: Optional[str]


class FanState(BaseModel):
    """Fan state model."""

    class_name: Literal["Fan", "FanGroup"]
    preset_mode: Optional[
        str
    ]  # TODO: how should we represent these when they are None?
    percentage: Optional[int]  # TODO: how should we represent these when they are None?
    is_on: bool
    speed: Optional[str]


class LockState(BaseModel):
    """Lock state model."""

    class_name: Literal["Lock"] = "Lock"
    is_locked: bool


class BatteryState(BaseModel):
    """Battery state model."""

    class_name: Literal["Battery"] = "Battery"
    state: Optional[Union[str, float, int]]
    battery_size: Optional[str]
    battery_quantity: Optional[int]
    battery_voltage: Optional[float]


class ElectricalMeasurementState(BaseModel):
    """Electrical measurement state model."""

    class_name: Literal[
        "ElectricalMeasurement",
        "ElectricalMeasurementApparentPower",
        "ElectricalMeasurementRMSCurrent",
        "ElectricalMeasurementRMSVoltage",
    ]
    state: Optional[Union[str, float, int]]
    measurement_type: Optional[str]
    active_power_max: Optional[str]
    rms_current_max: Optional[str]
    rms_voltage_max: Optional[str]


class LightState(BaseModel):
    """Light state model."""

    class_name: Literal["Light", "HueLight", "ForceOnLight", "LightGroup"]
    on: bool
    brightness: Optional[int]
    hs_color: Optional[tuple[float, float]]
    color_temp: Optional[int]
    effect: Optional[str]
    off_brightness: Optional[int]


class SwitchState(BaseModel):
    """Switch state model."""

    class_name: Literal["Switch", "SwitchGroup"]
    state: bool


class SmareEnergyMeteringState(BaseModel):
    """Smare energy metering state model."""

    class_name: Literal["SmartEnergyMetering", "SmartEnergySummation"]
    state: Optional[Union[str, float, int]]
    device_type: Optional[str]
    status: Optional[str]


class BaseEntity(BaseEventedModel):
    """Base platform entity model."""

    name: str
    unique_id: str
    platform: str
    class_name: str


class BasePlatformEntity(BaseEntity):
    """Base platform entity model."""

    device_ieee: str
    endpoint_id: int


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
    zone_type: Optional[int]
    state: BooleanState


class BaseSensorEntity(BasePlatformEntity):
    """Sensor model."""

    attribute: Optional[str]
    decimals: int
    divisor: int
    multiplier: Union[int, float]
    unit: Optional[int]


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
        "LastSeenSensor",
    ]
    state: GenericState


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
    state: GenericState


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
    speed_list: list[str]
    percentage_step: float
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
    engineer_units: Optional[int]  # TODO: how should we represent this when it is None?
    application_type: Optional[
        int
    ]  # TODO: how should we represent this when it is None?
    step: Optional[float]  # TODO: how should we represent this when it is None?
    min_value: float
    max_value: float
    name: str
    state: GenericState


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
    state: GenericState


class ThermostatEntity(BasePlatformEntity):  # TODO fix this
    """Thermostat entity model."""

    class_name: Literal[
        "Thermostat",
        "SinopeTechnologiesThermostat",
        "ZenWithinThermostat",
        "MoesThermostat",
        "BecaThermostat",
    ]
    state: GenericState  # TODO fix this


class SirenEntity(BasePlatformEntity):
    """Siren entity model."""

    class_name: Literal["Siren"]
    available_tones: Optional[Union[list[Union[int, str]], dict[int, str]]]
    supported_features: int
    state: BooleanState


class SwitchEntity(BasePlatformEntity):
    """Switch entity model."""

    class_name: Literal["Switch"]
    state: SwitchState


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
    device_type: Literal["Coordinator", "Router", "EndDevice"]
    signature: DeviceSignature


class Device(BaseDevice):
    """Device model."""

    entities: dict[
        str,
        Annotated[
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
                ThermostatEntity,
            ],
            Field(discriminator="class_name"),  # noqa: F821
        ],
    ]
    neighbors: list[Any]
    device_automation_triggers: dict[str, dict[str, Any]]


class GroupEntity(BaseEntity):
    """Group entity model."""

    group_id: int
    state: Any


class LightGroupEntity(GroupEntity):
    """Group entity model."""

    class_name: Literal["LightGroup"]
    state: LightState


class FanGroupEntity(GroupEntity):
    """Group entity model."""

    class_name: Literal["FanGroup"]
    state: FanState


class SwitchGroupEntity(GroupEntity):
    """Group entity model."""

    class_name: Literal["SwitchGroup"]
    state: SwitchState


class GroupMember(BaseModel):
    """Group member model."""

    endpoint_id: int
    device: Device
    entities: dict[
        str,
        Annotated[
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
                ThermostatEntity,
            ],
            Field(discriminator="class_name"),  # noqa: F821
        ],
    ]


class Group(BaseModel):
    """Group model."""

    name: str
    id: int
    members: dict[str, GroupMember]
    entities: dict[
        str,
        Annotated[
            Union[LightGroupEntity, FanGroupEntity, SwitchGroupEntity],
            Field(discriminator="class_name"),  # noqa: F821
        ],
    ]


class GroupMemberReference(BaseModel):
    """Group member reference model."""

    ieee: str
    endpoint_id: int
