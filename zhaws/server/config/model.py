"""Configuration models for the zhaws server."""

from typing import Any

from zha.application.helpers import ZHAConfiguration
from zhaws.model import BaseModel


class ServerConfiguration(BaseModel):
    """Server configuration for zhaws."""

    host: str = "0.0.0.0"
    port: int = 8001
    network_auto_start: bool = False
    zha_config: ZHAConfiguration
    zigpy_config: dict[str, Any]
