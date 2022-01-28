"""Proxy object for the client side objects."""
from __future__ import annotations

from typing import TYPE_CHECKING

from zhaws.client.model.events import PlatformEntityEvent
from zhaws.client.model.types import ButtonEntity
from zhaws.event import EventBase

if TYPE_CHECKING:
    from zhaws.client.client import Client
    from zhaws.client.controller import Controller
    from zhaws.client.model.types import Device as DeviceModel, Group as GroupModel


class BaseProxyObject(EventBase):
    """BaseProxyObject for the zhaws.client."""

    def __init__(self, controller: Controller, client: Client):
        """Initialize the BaseProxyObject class."""
        super().__init__()
        self._controller: Controller = controller
        self._client: Client = client
        self._proxied_object: GroupModel | DeviceModel

    @property
    def controller(self) -> Controller:
        """Return the controller."""
        return self._controller

    @property
    def client(self) -> Client:
        """Return the client."""
        return self._client

    def emit_platform_entity_event(self, event: PlatformEntityEvent) -> None:
        """Proxy the firing of an entity event."""
        entity = self._proxied_object.entities.get(event.platform_entity.unique_id)
        if entity is None:
            raise ValueError("Entity not found: %s", event.platform_entity.unique_id)
        if not isinstance(entity, ButtonEntity):
            entity.state = event.state
        self.emit(f"{event.platform_entity.unique_id}_{event.event}", event)


class GroupProxy(BaseProxyObject):
    """Group proxy for the zhaws.client."""

    def __init__(self, group: GroupModel, controller: Controller, client: Client):
        """Initialize the GroupProxy class."""
        super().__init__(controller, client)
        self._proxied_object: GroupModel = group

    @property
    def group(self) -> GroupModel:
        """Return the group."""
        return self._proxied_object

    @group.setter
    def group(self, group: GroupModel) -> None:
        """Set the group."""
        self._proxied_object = group

    def __repr__(self) -> str:
        return self._proxied_object.__repr__()


class DeviceProxy(BaseProxyObject):
    """Device proxy for the zhaws.client."""

    def __init__(self, device: DeviceModel, controller: Controller, client: Client):
        """Initialize the DeviceProxy class."""
        super().__init__(controller, client)
        self._proxied_object: DeviceModel = device

    @property
    def device(self) -> DeviceModel:
        """Return the device."""
        return self._proxied_object

    @device.setter
    def device(self, device: DeviceModel) -> None:
        """Set the device."""
        self._proxied_object = device

    def __repr__(self) -> str:
        return self._proxied_object.__repr__()
