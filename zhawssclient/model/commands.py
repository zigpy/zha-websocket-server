"""Models that represent commands and command responses."""

from typing import Annotated, Dict, Literal, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.types import Device


class CommandResponse(BaseModel):
    """Command response model."""

    message_type: Literal["result"] = "result"
    message_id: int
    success: bool


class DefaultResponse(CommandResponse):
    """Get devices response."""

    command: Literal["start_network", "stop_network", "remove_device", "stop_server"]


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
