"""PrebuiltArtifacts  -  wrap already-compiled files in the manifest as artifacts."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Generator, final

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
        Any,
        dict[str, Artifact],
        PrebuiltArtifactsError,
        PrebuiltArtifactsData,
        Unreachable,
    ]
):
    """Inject already-built files into the artifact dict.

    ``file_map`` maps artifact name to either:

    - a ``str`` -- path relative to ``manifest.root`` (only valid when the
      pipeline input is a ``Manifest`` or ``MakefileManifest``).
    - an absolute ``Path`` -- used as-is; valid after any build step.

    If ``make_executable`` is True (default), the user execute bit is set on
    each file.

    When the pipeline input is a ``dict[str, Artifact]`` (e.g. after
    ``MakefileBuild``), the existing artifacts are preserved and the new ones
    are merged in.  Relative ``str`` paths are not allowed in this case since
    there is no manifest root to resolve against -- use an absolute ``Path``.
    """

    def __init__(
        self,
        file_map: dict[str, str | Path],
        make_executable: bool = True,
    ) -> None:
        self._file_map = file_map
        self._make_executable = make_executable

    def __call__(
        self, input: Any
    ) -> Generator[
        Result[PrebuiltArtifactsData, Unreachable],
        None,
        Result[dict[str, Artifact], PrebuiltArtifactsError],
    ]:
        root: Path | None = getattr(input, "root", None)
        existing: dict[str, Artifact] = dict(input) if isinstance(input, dict) else {}
        artifacts: dict[str, Artifact] = dict(existing)

        for name, path_spec in self._file_map.items():
            if isinstance(path_spec, str):
                if root is None:
                    return Err(
                        PrebuiltArtifactsError(
                            file=path_spec,
                            message=(
                                f"Relative path '{path_spec}' requires a Manifest input. "
                                "Use an absolute Path when chaining after a build step."
                            ),
                        )
                    )
                path = root / path_spec
            else:
                path = path_spec

            if self._make_executable:
                try:
                    current = path.stat().st_mode
                    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError as exc:
                    return Err(
                        PrebuiltArtifactsError(
                            file=str(path_spec),
                            message=f"Could not chmod '{path}': {exc}",
                        )
                    )
            try:
                artifacts[name] = FileArtifact(path=path)
            except Exception as exc:
                return Err(
                    PrebuiltArtifactsError(
                        file=str(path_spec),
                        message=str(exc),
                    )
                )

        yield Ok(PrebuiltArtifactsData(artifact_names=list(artifacts.keys())))
        return Ok(artifacts)


import lograder.output.layout.pipeline.prebuilt  # noqa: E402, F401
