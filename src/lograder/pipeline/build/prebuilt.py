"""PrebuiltArtifacts  -  wrap already-compiled files in the manifest as artifacts."""

from __future__ import annotations

import stat
from typing import Generator, final

from pydantic import BaseModel

from lograder.common import Err, Ok, Result, Unreachable
from lograder.pipeline.build.build import Build
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.pipeline.types.parcels import Manifest


class PrebuiltArtifactsData(BaseModel):
    """Informational packet: files successfully wrapped as artifacts."""

    artifact_names: list[str]


class PrebuiltArtifactsError(BaseModel):
    """Fatal packet: a file could not be wrapped as an artifact."""

    file: str
    message: str


@final
class PrebuiltArtifacts(
    Build[
        Manifest,
        dict[str, Artifact],
        PrebuiltArtifactsError,
        PrebuiltArtifactsData,
        Unreachable,
    ]
):
    """Convert manifest files directly into a dict of FileArtifacts.

    ``file_map`` maps artifact name -> path relative to ``manifest.root``.
    If ``make_executable`` is True (default), sets the user execute bit on
    each file so that executables and bash scripts can be invoked without a
    separate chmod step.
    """

    def __init__(
        self,
        file_map: dict[str, str],
        make_executable: bool = True,
    ) -> None:
        self._file_map = file_map
        self._make_executable = make_executable

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[PrebuiltArtifactsData, Unreachable],
        None,
        Result[dict[str, Artifact], PrebuiltArtifactsError],
    ]:
        artifacts: dict[str, Artifact] = {}

        for name, rel_path in self._file_map.items():
            path = manifest.root / rel_path
            if self._make_executable:
                try:
                    current = path.stat().st_mode
                    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError as exc:
                    return Err(
                        PrebuiltArtifactsError(
                            file=rel_path,
                            message=f"Could not chmod '{path}': {exc}",
                        )
                    )
            try:
                artifacts[name] = FileArtifact(path=path)
            except Exception as exc:
                return Err(
                    PrebuiltArtifactsError(
                        file=rel_path,
                        message=str(exc),
                    )
                )

        yield Ok(PrebuiltArtifactsData(artifact_names=list(artifacts.keys())))
        return Ok(artifacts)
