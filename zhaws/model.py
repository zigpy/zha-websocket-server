"""Shared models for zhaws."""
import logging
from typing import TYPE_CHECKING, Any, Literal, Optional, Union, no_type_check

from pydantic import BaseModel as PydanticBaseModel, validator
from zigpy.types.named import EUI64

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

_LOGGER = logging.getLogger(__name__)


class BaseModel(PydanticBaseModel):
    """Base model for zhawss models."""

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @validator("ieee", pre=True, always=True, each_item=False, check_fields=False)
    def convert_ieee(
        cls, ieee: Optional[Union[str, EUI64]], values: dict[str, Any], **kwargs: Any
    ) -> Optional[EUI64]:
        if ieee is None:
            return None
        if isinstance(ieee, str):
            return EUI64.convert(ieee)
        return ieee

    @validator(
        "device_ieee", pre=True, always=True, each_item=False, check_fields=False
    )
    def convert_device_ieee(
        cls,
        device_ieee: Optional[Union[str, EUI64]],
        values: dict[str, Any],
        **kwargs: Any
    ) -> Optional[EUI64]:
        if device_ieee is None:
            return None
        if isinstance(device_ieee, str):
            return EUI64.convert(device_ieee)
        return device_ieee

    @classmethod
    @no_type_check
    def _get_value(
        cls,
        v: Any,
        to_dict: bool,
        by_alias: bool,
        include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]],
        exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]],
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
    ) -> Any:
        """custom get value."""
        if isinstance(v, EUI64):
            return str(v)
        return PydanticBaseModel._get_value(
            v,
            to_dict,
            by_alias,
            include,
            exclude,
            exclude_unset,
            exclude_defaults,
            exclude_none,
        )


class BaseEvent(BaseModel):
    """Base event model."""

    message_type: Literal["event"] = "event"
    event_type: str
    event: str
