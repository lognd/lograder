from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from lograder.process.executable import StaticExecutable, ExecutableInput, ExecutableOptions, ExecutableOutput


class Artifact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

T = TypeVar("T")
O = TypeVar("O")
class RunnableArtifact(Artifact, Generic[T, O], ABC):
    @abstractmethod
    def __call__(self, input: T) -> O: ...

class ExecutableArtifact(RunnableArtifact[tuple[ExecutableInput, ExecutableOptions], ExecutableOutput]):
    def __call__(self, input: tuple[ExecutableInput, ExecutableOptions]) -> ExecutableOutput: ...
        # TODO: implement running logic.

class FileArtifact(Artifact):
    path: Path

    @field_validator("path", mode="after")
    @classmethod
    def validate_file_exists(cls, path: Path) -> Path:
        if not path.is_file():
            raise ValueError(f"File, `{path}`, does not exist.")
        return path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def text(self) -> str:
        return self.path.read_text()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def binary(self) -> bytes:
        return self.path.read_bytes()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def executable(self) -> StaticExecutable:
        return StaticExecutable([str(self.path.resolve())])


class CMakeArtifact(Artifact):
    name: str
    target_type: str
    target_id: str | None = None
    target_json: Path | None = None
    config_name: str | None = None
    project_name: str | None = None
    source_dir: Path | None = None
    build_dir: Path
    raw_target: dict[str, Any] = Field(default_factory=dict)


class CMakeFileArtifact(CMakeArtifact, FileArtifact):
    artifact_path_from_cmake: str
