"""Shared models for zhaws."""

from typing import Literal

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """Base model for zhawss models."""

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class BaseEvent(BaseModel):
    """Base event model."""

    message_type: Literal["event"] = "event"
    event_type: str
    event: str
