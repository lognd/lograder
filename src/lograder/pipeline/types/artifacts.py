from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Artifact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
