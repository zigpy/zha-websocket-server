"""Configuration utilities for the zhaws server."""
from __future__ import annotations

from zhaws.server.config.model import ServerConfiguration


def zigpy_config(config: ServerConfiguration) -> dict:
    """Return a dict representing the zigpy configuration from the zhaws ServerCOnfiguration."""
    return {
        "database_path": config.zigpy_configuration.database_path,
        "device": config.radio_configuration.dict(exclude={"type": True}),
    }
