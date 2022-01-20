"""Group for the zhaws.client."""
from __future__ import annotations

from typing import TYPE_CHECKING

from zhaws.event import EventBase

if TYPE_CHECKING:
    from zhaws.client.client import Client
    from zhaws.client.controller import Controller
    from zhaws.client.model.types import Group as GroupModel


class Group(EventBase):
    """Group for the zhaws.client."""

    def __init__(self, group: GroupModel, controller: Controller, client: Client):
        """Initialize the Group class."""
        super().__init__()
        self._group: GroupModel = group
        self._controller: Controller = controller
        self._client: Client = client

    @property
    def group(self) -> GroupModel:
        """Return the group."""
        return self._group

    @group.setter
    def group(self, group: GroupModel) -> None:
        """Set the group."""
        self._group = group

    @property
    def controller(self) -> Controller:
        """Return the controller."""
        return self._controller

    @property
    def client(self) -> Client:
        """Return the client."""
        return self._client

    def __repr__(self) -> str:
        return self._group.__repr__()
