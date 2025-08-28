from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, field_validator

AscendingOrder = Literal["asc"]

class LeaderboardEntry(BaseModel):
    name: str
    value: float | str
    order: Optional[AscendingOrder] = None

    @field_validator("value")
    def validate_value(cls, v):
        if isinstance(v, str) and any([char != '*' for char in v]):
            raise ValueError("If passing a string for value, it must be made entirely of the character, '*'.")
        return v