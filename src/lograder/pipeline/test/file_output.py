from collections.abc import Iterable
from pathlib import Path
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.output_compare import (
    ComparisonMode,
    compare_outputs,
    make_unified_diff,
)
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import ExecutableInput, ExecutableOptions


class FileOutputCase(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    stdin: bytes = b""
    output_file: Path
    expected_content: str = ""
    comparison: ComparisonMode = ComparisonMode.STRIP
    expected_exit_code: int | None = None


class FileOutputSuccess(TestSuccess):
    args: list[str]
    output_file: Path


class FileOutputFailure(TestFailure):
    args: list[str]
    output_file: Path
    stdin_text: str
    expected_content: str
    actual_content: str | None
    diff: str
    expected_exit_code: int | None
    actual_exit_code: int


class FileOutputError(TestError):
    pass


@final
class FileOutputTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        FileOutputError,
        FileOutputSuccess,
        FileOutputFailure,
    ]
):
    def __init__(
        self,
        artifact_name: str,
        test_cases: Iterable[FileOutputCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._test_cases = test_cases
        self._options = options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[FileOutputSuccess, FileOutputFailure],
        None,
        Result[dict[str, Artifact], FileOutputError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if artifact is None:
            return Err(
                FileOutputError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact `{self._artifact_name}` not found. "
                        f"Available: {sorted(artifacts)}."
                    ),
                )
            )
        if not isinstance(artifact, FileArtifact):
            return Err(
                FileOutputError(
                    artifact_name=self._artifact_name,
                    message=f"Artifact `{self._artifact_name}` exists but is not a file; cannot execute it.",
                )
            )

        options = self._options or ExecutableOptions()

        for case in self._test_cases:
            out_path = (
                case.output_file
                if case.output_file.is_absolute()
                else options.cwd / case.output_file
            )
            if out_path.exists():
                out_path.unlink()

            inp = ExecutableInput(stdin_bytes=case.stdin, arguments=case.args)
            output = artifact.executable(inp, options=options)

            actual_content: str | None = None
            if out_path.exists():
                actual_content = out_path.read_text(encoding="utf-8", errors="replace")

            file_ok = actual_content is not None and compare_outputs(
                actual_content, case.expected_content, case.comparison
            )
            exit_ok = (
                case.expected_exit_code is None
                or output.return_code == case.expected_exit_code
            )

            if file_ok and exit_ok:
                yield Ok(
                    FileOutputSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        output_file=case.output_file,
                    )
                )
            else:
                diff = (
                    make_unified_diff(case.expected_content, actual_content)
                    if actual_content is not None and not file_ok
                    else ""
                )
                yield Err(
                    FileOutputFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        output_file=case.output_file,
                        stdin_text=case.stdin.decode("utf-8", errors="replace"),
                        expected_content=case.expected_content,
                        actual_content=actual_content,
                        diff=diff,
                        expected_exit_code=case.expected_exit_code,
                        actual_exit_code=output.return_code,
                    )
                )

        return Ok(artifacts)
