"""Models for zhawss."""

import orjson
from pydantic import BaseModel as PydanticBaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class BaseModel(PydanticBaseModel):
    """Base model for zhawss models."""

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
