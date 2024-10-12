"""Models for platform things."""

from typing import Final, Literal, Optional

from zigpy.types.named import EUI64

from zhaws.model import BaseEvent

STATE_CHANGED: Final[Literal["state_changed"]] = "state_changed"


class EntityStateChangedEvent(BaseEvent):
    """Event for when an entity state changes."""

    event_type: Literal["entity"] = "entity"
    event: Literal["state_changed"] = STATE_CHANGED
    platform: str
    unique_id: str
    device_ieee: Optional[EUI64] = None
    endpoint_id: Optional[int] = None
    group_id: Optional[int] = None
