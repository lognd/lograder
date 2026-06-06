"""BashScriptBuild  -  run a student-submitted bash script then collect artifacts."""

from __future__ import annotations

import stat
from typing import Generator, final

from pydantic import BaseModel, ConfigDict

from lograder.common import Err, Ok, Result, Unreachable
from lograder.pipeline.build.build import Build
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.pipeline.types.parcels import Manifest
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.bash import BashExecutable, BashScriptArgs


class BashScriptBuildOutput(BaseModel):
    """Non-fatal packet: the script ran (regardless of exit code)."""

    model_config = ConfigDict(arbitrary_types_allowed=False)

    script: str
    return_code: int
    stdout: str
    stderr: str


class BashScriptBuildError(BaseModel):
    """Fatal packet: script failed or an expected artifact was not produced."""

    script: str
    message: str
    return_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None


@final
class BashScriptBuild(
    Build[
        Manifest,
        dict[str, Artifact],
        BashScriptBuildError,
        BashScriptBuildOutput,
        Unreachable,
    ]
):
    """Run a student-submitted bash script, then wrap the outputs as artifacts.

    The script is executed with ``bash <script>`` (no execute bit required on
    the submitted file). ``cwd`` defaults to ``manifest.root``.

    ``artifacts`` maps artifact name -> path **relative to cwd**. After the
    script succeeds, each path is resolved and wrapped as a ``FileArtifact``.
    If ``make_artifacts_executable`` is ``True`` (the default), the user/group/
    other execute bits are set on each collected artifact.

    Fatal errors (``Err`` return):
    - ``bash`` is not installed
    - The script file is missing from the manifest
    - The script exits non-zero
    - An expected artifact path does not exist after the script runs

    A single non-fatal ``Ok(BashScriptBuildOutput)`` is yielded on success so
    the grader can inspect stdout/stderr in the HTML report.
    """

    def __init__(
        self,
        script: str,
        artifacts: dict[str, str],
        options: ExecutableOptions | None = None,
        make_artifacts_executable: bool = True,
    ) -> None:
        self._script = script
        self._artifacts = artifacts
        self._options = options
        self._make_artifacts_executable = make_artifacts_executable

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[BashScriptBuildOutput, Unreachable],
        None,
        Result[dict[str, Artifact], BashScriptBuildError],
    ]:
        script_path = manifest.root / self._script
        if not script_path.exists():
            return Err(
                BashScriptBuildError(
                    script=self._script,
                    message=f"Script not found: {script_path}",
                )
            )

        bash = BashExecutable()
        runnable = bash.check_runnable()
        if runnable.is_err:
            return Err(
                BashScriptBuildError(
                    script=self._script,
                    message=f"bash is not available: {runnable.danger_err.message}",
                )
            )

        cwd = (self._options.cwd if self._options else None) or manifest.root
        options = (self._options or ExecutableOptions()).model_copy(
            update={
                "cwd": cwd,
                "stdout_mode": StreamMode.PIPE,
                "stderr_mode": StreamMode.PIPE,
            }
        )

        result = bash(BashScriptArgs(script=script_path), options=options)
        if result.is_err:
            return Err(
                BashScriptBuildError(
                    script=self._script,
                    message=f"Failed to invoke bash: {result.danger_err.message}",
                )
            )

        out = result.danger_ok
        if out.return_code != 0:
            return Err(
                BashScriptBuildError(
                    script=self._script,
                    message=f"Script exited with code {out.return_code}.",
                    return_code=out.return_code,
                    stdout=out.stdout_text,
                    stderr=out.stderr_text,
                )
            )

        yield Ok(
            BashScriptBuildOutput(
                script=self._script,
                return_code=out.return_code,
                stdout=out.stdout_text,
                stderr=out.stderr_text,
            )
        )

        artifact_map: dict[str, Artifact] = {}
        for name, rel in self._artifacts.items():
            path = (cwd / rel).resolve()
            if not path.exists():
                return Err(
                    BashScriptBuildError(
                        script=self._script,
                        message=f"Expected artifact '{rel}' was not produced by the script.",
                        return_code=out.return_code,
                        stdout=out.stdout_text,
                        stderr=out.stderr_text,
                    )
                )
            if self._make_artifacts_executable:
                try:
                    current = path.stat().st_mode
                    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError as exc:
                    return Err(
                        BashScriptBuildError(
                            script=self._script,
                            message=f"Could not chmod '{path}': {exc}",
                        )
                    )
            artifact_map[name] = FileArtifact(path=path)

        return Ok(artifact_map)


