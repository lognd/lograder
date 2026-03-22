from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from lograder.pipeline.types.executable.base_executable import Executable


class Artifact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutableArtifact(Executable): ...
