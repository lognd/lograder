import difflib
from enum import Enum
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import ExecutableInput, ExecutableOptions


class ComparisonMode(str, Enum):
    EXACT = "exact"
    STRIP = "strip"
    IGNORE_TRAILING_WHITESPACE = "ignore_trailing_whitespace"


def compare_outputs(actual: str, expected: str, mode: ComparisonMode) -> bool:
    if mode == ComparisonMode.EXACT:
        return actual == expected
    if mode == ComparisonMode.STRIP:
        return actual.strip() == expected.strip()
    if mode == ComparisonMode.IGNORE_TRAILING_WHITESPACE:
        return [line.rstrip() for line in actual.splitlines()] == [
            line.rstrip() for line in expected.splitlines()
        ]
    return actual == expected


def make_unified_diff(expected: str, actual: str) -> str:
    lines = difflib.unified_diff(
        expected.splitlines(keepends=True),
        actual.splitlines(keepends=True),
        fromfile="expected",
        tofile="actual",
    )
    return "".join(lines)


class OutputCompareCase(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    stdin: bytes = b""
    expected_stdout: str = ""
    comparison: ComparisonMode = ComparisonMode.STRIP
    expected_exit_code: int | None = None


class OutputCompareSuccess(TestSuccess):
    args: list[str]


class OutputCompareFailure(TestFailure):
    args: list[str]
    stdin_text: str
    expected_stdout: str
    actual_stdout: str
    diff: str
    expected_exit_code: int | None
    actual_exit_code: int


class OutputCompareError(TestError):
    pass


@final
class OutputCompareTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        OutputCompareError,
        OutputCompareSuccess,
        OutputCompareFailure,
    ]
):
    def __init__(
        self,
        artifact_name: str,
        test_cases: list[OutputCompareCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._test_cases = test_cases
        self._options = options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[OutputCompareSuccess, OutputCompareFailure],
        None,
        Result[dict[str, Artifact], OutputCompareError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if artifact is None:
            return Err(
                OutputCompareError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact `{self._artifact_name}` not found. "
                        f"Available: {sorted(artifacts)}."
                    ),
                )
            )
        if not isinstance(artifact, FileArtifact):
            return Err(
                OutputCompareError(
                    artifact_name=self._artifact_name,
                    message=f"Artifact `{self._artifact_name}` exists but is not a file; cannot execute it.",
                )
            )

        options = self._options or ExecutableOptions()

        for case in self._test_cases:
            inp = ExecutableInput(stdin_bytes=case.stdin, arguments=case.args)
            output = artifact.executable(inp, options=options)

            stdout_ok = compare_outputs(
                output.stdout_text, case.expected_stdout, case.comparison
            )
            exit_ok = (
                case.expected_exit_code is None
                or output.return_code == case.expected_exit_code
            )

            if stdout_ok and exit_ok:
                yield Ok(
                    OutputCompareSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                    )
                )
            else:
                yield Err(
                    OutputCompareFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        stdin_text=case.stdin.decode("utf-8", errors="replace"),
                        expected_stdout=case.expected_stdout,
                        actual_stdout=output.stdout_text,
                        diff=(
                            make_unified_diff(case.expected_stdout, output.stdout_text)
                            if not stdout_ok
                            else ""
                        ),
                        expected_exit_code=case.expected_exit_code,
                        actual_exit_code=output.return_code,
                    )
                )

        return Ok(artifacts)
