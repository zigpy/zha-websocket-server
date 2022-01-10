"""Models that represent commands and command responses."""

from typing import Annotated, Dict, Literal, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.types import Device


class CommandResponse(BaseModel):
    """Command response model."""

    message_type: Literal["result"] = "result"


class StartNetworkResponse(CommandResponse):
    """Get devices response."""

    command: Literal["start_network"] = "start_network"


class GetDevicesResponse(CommandResponse):
    """Get devices response."""

    command: Literal["get_devices"] = "get_devices"
    devices: Dict[str, Device] = None


CommandResponse = Annotated[
    Union[GetDevicesResponse, StartNetworkResponse],
    Field(discriminator="command"),  # noqa: F821
]
