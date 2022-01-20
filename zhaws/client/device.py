"""Device for the zhaws.client."""
from __future__ import annotations

from typing import TYPE_CHECKING

from zhaws.event import EventBase

if TYPE_CHECKING:
    from zhaws.client.client import Client
    from zhaws.client.controller import Controller
    from zhaws.client.model.types import Device as DeviceModel


class Device(EventBase):
    """Device for the zhaws.client."""

    def __init__(self, device: DeviceModel, controller: Controller, client: Client):
        """Initialize the Device class."""
        super().__init__()
        self._device: DeviceModel = device
        self._controller: Controller = controller
        self._client: Client = client

    @property
    def device(self) -> DeviceModel:
        """Return the device."""
        return self._device

    @device.setter
    def device(self, device: DeviceModel) -> None:
        """Set the device."""
        self._device = device

    @property
    def controller(self) -> Controller:
        """Return the controller."""
        return self._controller

    @property
    def client(self) -> Client:
        """Return the client."""
        return self._client

    def __repr__(self) -> str:
        return self._device.__repr__()
