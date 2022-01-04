"""Typing helpers for zhawss."""
from typing import TYPE_CHECKING

ClientType = "Client"
ClientManagerType = "ClientManagerType"
ServerType = "Server"


if TYPE_CHECKING:
    from zhawss.websocket.client import Client, ClientManager
    from zhawss.websocket.server import Server

    ClientType = Client
    ClientManagerType = ClientManager
    ServerType = Server
