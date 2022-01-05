"""Types for zhawss."""
from typing import TYPE_CHECKING

ControllerType = "Controller"
DeviceType = "Device"
EndpointType = "Endpoint"
DeviceStatusType = "DeviceStatus"

if TYPE_CHECKING:
    from zhawss.zigbee.controller import Controller
    from zhawss.zigbee.device import Device, DeviceStatus
    from zhawss.zigbee.endpoint import Endpoint

    ControllerType = Controller
    DeviceType = Device
    EndpointType = Endpoint
    DeviceStatusType = DeviceStatus
