"""Models that represent messages in zhawss."""
from typing import Annotated, Union

from pydantic.fields import Field

from zhawssclient.model import BaseModel
from zhawssclient.model.commands import CommandResponses
from zhawssclient.model.events import Events


class Message(BaseModel):
    """Response model."""

    __root__: Annotated[
        Union[CommandResponses, Events],
        Field(discriminator="message_type"),  # noqa: F821
    ]
