"""Types for zhawss."""
from typing import TYPE_CHECKING

ControllerType = "Controller"
DeviceType = "Device"
EndpointType = "Endpoint"
DeviceStatusType = "DeviceStatus"

if TYPE_CHECKING:
    from zhaws.server.zigbee.controller import Controller
    from zhaws.server.zigbee.device import Device, DeviceStatus
    from zhaws.server.zigbee.endpoint import Endpoint

    ControllerType = Controller
    DeviceType = Device
    EndpointType = Endpoint
    DeviceStatusType = DeviceStatus
