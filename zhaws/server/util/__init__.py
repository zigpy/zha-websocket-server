"""Utility classes for zhawss."""
import logging
from typing import Any


class LogMixin:
    """Log helper."""

    def log(self, level: int, msg: str, *args: Any) -> None:
        """Log with level."""
        raise NotImplementedError

    def debug(self, msg: str, *args: Any) -> None:
        """Debug level log."""
        return self.log(logging.DEBUG, msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        """Info level log."""
        return self.log(logging.INFO, msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        """Warning method log."""
        return self.log(logging.WARNING, msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        """Error level log."""
        return self.log(logging.ERROR, msg, *args)
