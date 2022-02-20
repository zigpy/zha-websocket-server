"""Configuration models for the zhaws server."""

from typing import Annotated, Literal, Union

from pydantic import Field

from zhaws.model import BaseModel


class BaseRadioConfiguration(BaseModel):
    """Base zigbee radio configuration for zhaws."""

    type: Literal["ezsp", "xbee", "deconz", "zigate", "znp"]
    path: str = "/dev/tty.SLAB_USBtoUART"


class EZSPRadioConfiguration(BaseRadioConfiguration):
    """EZSP radio configuration for zhaws."""

    type: Literal["ezsp"] = "ezsp"
    baudrate: int = 115200
    flow_control: Literal["hardware", "software"] = "hardware"


class XBeeRadioConfiguration(BaseRadioConfiguration):
    """XBee radio configuration for zhaws."""

    type: Literal["xbee"] = "xbee"


class DeconzRadioConfiguration(BaseRadioConfiguration):
    """Deconz radio configuration for zhaws."""

    type: Literal["deconz"] = "deconz"


class ZigateRadioConfiguration(BaseRadioConfiguration):
    """Zigate radio configuration for zhaws."""

    type: Literal["zigate"] = "zigate"


class ZNPRadioConfiguration(BaseRadioConfiguration):
    """ZNP radio configuration for zhaws."""

    type: Literal["znp"] = "znp"


class ZigpyConfiguration(BaseModel):
    """Zigpy configuration for zhaws."""

    database_path: str = "./zigbee.db"
    enable_quirks: bool = True


class ServerConfiguration(BaseModel):
    """Server configuration for zhaws."""

    host: str = "0.0.0.0"
    port: int = 8001
    network_auto_start: bool = False
    zigpy_configuration: ZigpyConfiguration = ZigpyConfiguration()
    radio_configuration: Annotated[
        Union[
            EZSPRadioConfiguration,
            XBeeRadioConfiguration,
            DeconzRadioConfiguration,
            ZigateRadioConfiguration,
            ZNPRadioConfiguration,
        ],
        Field(discriminator="type"),  # noqa: F821
    ] = EZSPRadioConfiguration()
