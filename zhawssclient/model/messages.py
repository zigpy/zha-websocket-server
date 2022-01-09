"""Models that represent messages in zhawss."""
from typing import Any, Literal

from zhawss.const import MessageTypes
from zhawssclient.model import BaseModel


class BaseMessage(BaseModel):
    """Message base class."""

    message_type: str


class BaseIncomingMessage(BaseMessage):
    """Incoming message base class."""

    command: str
    message_id: int


class BaseOutgoingMessage(BaseMessage):
    """Outgoing message base class."""

    message_id: int
    message_type: Literal["result"] = MessageTypes.RESULT


class BaseOutgoingResponseMessage(BaseOutgoingMessage):
    """Outgoing response message base class."""

    command: str
    data: Any
