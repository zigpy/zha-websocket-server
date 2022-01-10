"""Models that represent commands and command responses."""

from typing import Annotated, Dict, Literal, Union

from pydantic.fields import Field

from zhawssclient.model.messages import BaseOutgoingResponseMessage
from zhawssclient.model.types import Device


class StartNetworkResponse(BaseOutgoingResponseMessage):
    """Get devices response."""

    command: Literal["start_network"] = "start_network"


class GetDevicesResponse(BaseOutgoingResponseMessage):
    """Get devices response."""

    command: Literal["get_devices"] = "get_devices"
    devices: Dict[str, Device] = None


CommandResponse = Annotated[
    Union[GetDevicesResponse, StartNetworkResponse],
    Field(discriminator="command"),  # noqa: F821
]
