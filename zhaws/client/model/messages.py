"""Models that represent messages in zhawss."""

from typing import Annotated, Any, Optional, Union

from pydantic import RootModel, field_validator
from pydantic.fields import Field
from zigpy.types.named import EUI64

from zhaws.client.model.commands import CommandResponses
from zhaws.client.model.events import Events


class Message(RootModel):
    """Response model."""

    root: Annotated[
        Union[CommandResponses, Events],
        Field(discriminator="message_type"),  # noqa: F821
    ]

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
        return RootModel._get_value(cls, *args, **kwargs)
