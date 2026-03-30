from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lograder.process.executable import StaticExecutable


class Artifact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutableArtifact(Artifact):
    executable: StaticExecutable


class BinaryArtifact(Artifact): ...


class LibraryArtifact(Artifact): ...


class ObjectArtifact(BinaryArtifact): ...


class DynamicLibraryArtifact(BinaryArtifact, LibraryArtifact):
    dynamic_library: Path


class StaticLibraryArtifact(BinaryArtifact, LibraryArtifact):
    static_library: Path


class ModuleLibraryArtifact(BinaryArtifact, LibraryArtifact):
    module_library: Path
