"""Shared models for zhaws."""

import logging
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, field_validator
from zigpy.types.named import EUI64

_LOGGER = logging.getLogger(__name__)


class BaseModel(PydanticBaseModel):
    """Base model for zhawss models."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @field_validator("ieee", mode="before", check_fields=False)
    @classmethod
    def convert_ieee(cls, ieee: Optional[Union[str, EUI64]]) -> Optional[EUI64]:
        """Convert ieee to EUI64."""
        if ieee is None:
            return None
        if isinstance(ieee, str):
            return EUI64.convert(ieee)
        if isinstance(ieee, list):
            return EUI64(ieee)
        return ieee

    @field_validator("device_ieee", mode="before", check_fields=False)
    @classmethod
    def convert_device_ieee(
        cls, device_ieee: Optional[Union[str, EUI64]]
    ) -> Optional[EUI64]:
        """Convert device ieee to EUI64."""
        if device_ieee is None:
            return None
        if isinstance(device_ieee, str):
            return EUI64.convert(device_ieee)
        if isinstance(device_ieee, list):
            return EUI64(device_ieee)
        return device_ieee

    @classmethod
    def _get_value(cls, *args, **kwargs) -> Any:
        """Convert EUI64 to string."""
        value = args[0]
        if isinstance(value, EUI64):
            return str(value)
        return PydanticBaseModel._get_value(cls, *args, **kwargs)


class BaseEvent(BaseModel):
    """Base event model."""

    message_type: Literal["event"] = "event"
    event_type: str
    event: str
