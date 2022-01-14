"""Models that represent messages in zhawss."""
from typing import Annotated, Union

from pydantic.fields import Field

from zhaws.client.model import BaseModel
from zhaws.client.model.commands import CommandResponses
from zhaws.client.model.events import Events


class Message(BaseModel):
    """Response model."""

    __root__: Annotated[
        Union[CommandResponses, Events],
        Field(discriminator="message_type"),  # noqa: F821
    ]
