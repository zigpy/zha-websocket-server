"""Decorators for zhawss registries."""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

CALLABLE_T = TypeVar("CALLABLE_T", bound=Callable)  # pylint: disable=invalid-name


class DictRegistry(dict):
    """Dict Registry of items."""

    def register(
        self, name: int | str, item: str | CALLABLE_T = None
    ) -> Callable[[CALLABLE_T], CALLABLE_T]:
        """Return decorator to register item with a specific name."""

        def decorator(cluster_handler: CALLABLE_T) -> CALLABLE_T:
            """Register decorated cluster handler or item."""
            if item is None:
                self[name] = cluster_handler
            else:
                self[name] = item
            return cluster_handler

        return decorator


class SetRegistry(set):
    """Set Registry of items."""

    def register(self, name: int | str) -> Callable[[CALLABLE_T], CALLABLE_T]:
        """Return decorator to register item with a specific name."""

        def decorator(cluster_handler: CALLABLE_T) -> CALLABLE_T:
            """Register decorated cluster handler or item."""
            self.add(name)
            return cluster_handler

        return decorator
