"""JSON encoder for ZHA and Zigpy objects."""

import dataclasses
from datetime import datetime
from enum import Enum, StrEnum
import logging
from pathlib import Path
from typing import Any

import orjson
from zigpy.types import ListSubclass, Struct
from zigpy.types.basic import _IntEnumMeta
from zigpy.types.named import EUI64, NWK
from zigpy.zdo.types import NodeDescriptor

_LOGGER = logging.getLogger(__name__)


def json_encoder_default(obj: Any) -> Any:
    """Convert Home Assistant objects.

    Hand other objects to the original method.
    """
    if isinstance(obj, EUI64):
        return str(obj)
    if isinstance(obj, NWK):
        return repr(obj)
    if isinstance(obj, NodeDescriptor):
        return obj.as_dict()
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, type) and issubclass(obj, Struct):
        fields = obj._get_fields()
        dumped: dict[str, Any] = {
            "name": obj.__name__,
            "fields": [dataclasses.asdict(field) for field in fields],
        }
        for field in dumped["fields"]:
            del field["repr"]
            field["type"] = field["type"].__name__
            if field["dynamic_type"]:
                field["dynamic_type"] = field["dynamic_type"].__name__
        return dumped
    if isinstance(obj, ListSubclass):
        return list(obj)
    if isinstance(obj, _IntEnumMeta):
        return obj.__name__
    if isinstance(obj, StrEnum):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.name
    if hasattr(obj, "json_fragment"):
        return obj.json_fragment
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if isinstance(obj, float):
        return float(obj)
    if isinstance(obj, Path):
        return obj.as_posix()
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError


def dumps(data: Any) -> str:
    """Serialize data to a JSON formatted string."""
    try:
        message = orjson.dumps(
            data,
            default=json_encoder_default,
            option=orjson.OPT_PASSTHROUGH_SUBCLASS | orjson.OPT_NON_STR_KEYS,
        ).decode()
        return message
    except Exception as exc:
        raise ValueError(f"Couldn't serialize data: {data}") from exc


def loads(data: str) -> Any:
    """Deserialize data to a Python object."""
    try:
        return orjson.loads(data)
    except Exception as exc:
        raise ValueError(f"Couldn't deserialize data: {data}") from exc
