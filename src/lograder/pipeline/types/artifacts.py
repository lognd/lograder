from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .executable import Executable


class Artifact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutableArtifact(Executable): ...
