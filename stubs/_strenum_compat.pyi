# Just for compatibility.

from enum import Enum

class StrEnum(str, Enum): ...  # type: ignore[misc]