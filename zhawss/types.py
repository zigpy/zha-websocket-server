"""Typing helpers for zhawss."""
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

ClientType = "Client"
ClientManagerType = "ClientManagerType"
ControllerType = "Controller"
ServerType = "Server"

AsyncWebSocketCommandHandler = Callable[
    [ServerType, ClientType, Dict[str, Any]], Awaitable[None]
]
WebSocketCommandHandler = Callable[[ServerType, ClientType, Dict[str, Any]], None]


if TYPE_CHECKING:
    from zhawss.client import Client, ClientManager
    from zhawss.server import Server
    from zhawss.zigbee.application import Controller

    ClientType = Client
    ClientManagerType = ClientManager
    ControllerType = Controller
    ServerType = Server
