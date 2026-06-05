"""SymbolTest  -  verify exported symbols in object files, static/dynamic libraries."""

from __future__ import annotations

from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import ExecutableInput, ExecutableOptions
from lograder.process.parsers.nm import parse_nm_output
from lograder.process.registry.nm import NmArgs, NmExecutable

__test__: bool = False


class SymbolCase(BaseModel):
    __test__: bool = False
    name: str
    required: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    # Use -D to inspect dynamic symbol table (needed for shared libraries)
    dynamic: bool = False
    # Restrict to defined symbols only (excludes 'U'  -  undefined/external refs)
    defined_only: bool = True
    # Demangle C++ symbols before matching
    demangle: bool = False


class SymbolSuccess(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str
    found: list[str]  # names of required symbols that were found


class SymbolFailure(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str
    missing: list[str]  # required symbols not present
    present: list[str]  # forbidden symbols that were found


class SymbolError(TestError):
    __test__: bool = False


@final
class SymbolTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        SymbolError,
        SymbolSuccess,
        SymbolFailure,
    ]
):
    """Run ``nm`` on a FileArtifact and check for required/forbidden symbols.

    Yields ``Ok(SymbolSuccess)`` for passing cases and ``Err(SymbolFailure)``
    for failing cases. Returns ``Err(SymbolError)`` fatally if the artifact is
    missing or nm cannot run.
    """

    def __init__(
        self,
        artifact_name: str,
        cases: list[SymbolCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._cases = cases
        self._options = options or ExecutableOptions()

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[SymbolSuccess, SymbolFailure],
        None,
        Result[dict[str, Artifact], SymbolError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if not isinstance(artifact, FileArtifact):
            return Err(
                SymbolError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact '{self._artifact_name}' not found or is not a FileArtifact. "
                        f"Available: {list(artifacts.keys())}"
                    ),
                )
            )

        nm_exe = NmExecutable()
        runnable = nm_exe.check_runnable()
        if runnable.is_err:
            return Err(
                SymbolError(
                    artifact_name=self._artifact_name,
                    message=f"nm is not available: {runnable.danger_err.message}",
                )
            )

        for case in self._cases:
            nm_result = nm_exe(
                NmArgs(
                    files=[artifact.path],
                    dynamic=case.dynamic,
                    defined_only=case.defined_only,
                    demangle=case.demangle,
                ),
                options=self._options,
            )
            if nm_result.is_err:
                return Err(
                    SymbolError(
                        artifact_name=self._artifact_name,
                        message=f"nm failed for case '{case.name}': {nm_result.danger_err.message}",
                    )
                )

            output = nm_result.danger_ok
            if output.return_code != 0:
                return Err(
                    SymbolError(
                        artifact_name=self._artifact_name,
                        message=(
                            f"nm exited {output.return_code} for case '{case.name}': "
                            f"{output.stderr_text.strip()}"
                        ),
                    )
                )

            symbols = parse_nm_output(output.stdout_text)
            symbol_names = {s.name for s in symbols}

            missing = [s for s in case.required if s not in symbol_names]
            present = [s for s in case.forbidden if s in symbol_names]

            if missing or present:
                yield Err(
                    SymbolFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        missing=missing,
                        present=present,
                    )
                )
            else:
                yield Ok(
                    SymbolSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        found=[s for s in case.required if s in symbol_names],
                    )
                )

        return Ok(artifacts)
