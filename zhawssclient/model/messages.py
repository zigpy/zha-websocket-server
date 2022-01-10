"""Models that represent messages in zhawss."""
from typing import Annotated, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.commands import CommandResponse
from zhawssclient.model.events import Event

Messages = Annotated[
    Union[CommandResponse, Event],
    Field(discriminator="message_type"),  # noqa: F821
]


class Message(BaseModel):
    """Response model."""

    message_type: str
    message_id: int
    success: bool
    data: Messages
