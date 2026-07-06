from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

EventHandler = Callable[..., Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    async def emit(self, event_name: str, **payload: Any) -> None:
        for handler in self._handlers.get(event_name, []):
            result = handler(**payload)
            if result is not None:
                await result


event_bus = EventBus()
