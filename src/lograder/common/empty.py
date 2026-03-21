from __future__ import annotations

import inspect
from typing import final


class Empty:
    __slots__ = ()


@final
class Unreachable(Empty):
    def __new__(cls) -> Unreachable:
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None

            if caller is None:
                location = "unknown location"
            else:
                info = inspect.getframeinfo(caller)
                location = f"{info.filename}:{info.lineno} in {info.function}()"

            raise TypeError(
                f"`UNREACHABLE` was instantiated at {location}. "
                f"This sentinel should never be constructed at runtime."
            )
        finally:
            del frame
