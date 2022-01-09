"""Models that represent commands and command responses."""

from typing import Dict

from zigpy.types.named import EUI64

from zhawssclient.model.messages import BaseOutgoingResponseMessage
from zhawssclient.model.types import Device


class GetDevicesResponse(BaseOutgoingResponseMessage):
    """Get devices response."""

    command = "get_devices"
    devices: Dict[EUI64, Device] = None
