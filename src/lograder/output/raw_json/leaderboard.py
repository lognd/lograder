from typing import Optional

from pydantic import BaseModel, field_validator

from ..common import AscendingOrder


class LeaderboardJSON(BaseModel):
    name: str
    value: float | str
    order: Optional[AscendingOrder] = None

    @field_validator("value")
    def validate_value(cls, v):
        if isinstance(v, str) and any([char != "*" for char in v]):
            raise ValueError(
                "If passing a string for value, it must be made entirely of the character, '*'."
            )
        return v
