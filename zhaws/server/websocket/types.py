"""Typing helpers for zhawss."""
from typing import TYPE_CHECKING

ClientType = "Client"
ClientManagerType = "ClientManagerType"
ServerType = "Server"


if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client, ClientManager
    from zhaws.server.websocket.server import Server

    ClientType = Client
    ClientManagerType = ClientManager
    ServerType = Server
