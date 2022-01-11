"""Device for the zhawssclient."""

from zhawssclient.event import EventBase
from zhawssclient.model.types import ClientType, ControllerType, Device as DeviceModel


class Device(EventBase):
    """Device for the zhawssclient."""

    def __init__(
        self, device: DeviceModel, controller: ControllerType, client: ClientType
    ):
        """Initialize the Device class."""
        super().__init__()
        self._device: DeviceModel = device
        self._controller: ControllerType = controller
        self._client: ClientType = client

    @property
    def device(self) -> DeviceModel:
        """Return the device."""
        return self._device

    @property
    def controller(self) -> ControllerType:
        """Return the controller."""
        return self._controller

    @property
    def client(self) -> ClientType:
        """Return the client."""
        return self._client

    @device.setter
    def device(self, device: DeviceModel) -> None:
        """Set the device."""
        self._device = device
