"""Models that represent commands and command responses."""

from typing import Annotated, Dict, Literal, Optional, Tuple, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.types import Device


class Command(BaseModel):
    """Base class for command that are sent to the server."""

    command: str


class DeviceCommand(Command):
    """Base class for commands that address individual devices."""

    ieee: str


class PlatformEntityCommand(DeviceCommand):
    """Base class for commands that address individual platform entities."""

    unique_id: str


class LightTurnOnCommand(PlatformEntityCommand):
    """Command to instruct a light to turn on."""

    command: Literal["light_turn_on"] = "light_turn_on"
    brightness: Optional[int]
    transition: Optional[int]
    flash: Optional[Literal["long", "short"]]
    effect: Optional[str]
    hs_color: Optional[Tuple[float, float]]
    color_temp: Optional[int]


class LightTurnOffCommand(PlatformEntityCommand):
    """Command to instruct a light to turn off."""

    command: Literal["light_turn_off"] = "light_turn_off"
    transition: Optional[int]
    flash: Optional[Literal["long", "short"]]


class CommandResponse(BaseModel):
    """Command response model."""

    message_type: Literal["result"] = "result"
    message_id: int
    success: bool


class DefaultResponse(CommandResponse):
    """Get devices response."""

    command: Literal[
        "start_network",
        "stop_network",
        "remove_device",
        "stop_server",
        "light_turn_on",
        "light_turn_off",
    ]


class PermitJoiningResponse(CommandResponse):
    """Get devices response."""

    command: Literal["permit_joining"] = "permit_joining"
    duration: int


class GetDevicesResponse(CommandResponse):
    """Get devices response."""

    command: Literal["get_devices"] = "get_devices"
    devices: Dict[str, Device] = None


CommandResponses = Annotated[
    Union[DefaultResponse, GetDevicesResponse, PermitJoiningResponse],
    Field(discriminator="command"),  # noqa: F821
]
