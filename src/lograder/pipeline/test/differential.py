import difflib
from collections.abc import Iterable
from pathlib import Path
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.oracle import OracleInput
from lograder.pipeline.test.output_compare import compare_outputs
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    StaticExecutable,
)


def _make_diff(reference: str, student: str) -> str:
    lines = difflib.unified_diff(
        reference.splitlines(keepends=True),
        student.splitlines(keepends=True),
        fromfile="reference",
        tofile="student",
    )
    return "".join(lines)


class DifferentialSuccess(TestSuccess):
    args: list[str]


class DifferentialFailure(TestFailure):
    args: list[str]
    stdin_text: str
    student_stdout: str
    reference_stdout: str
    diff: str
    student_exit_code: int
    reference_exit_code: int


class DifferentialError(TestError):
    pass


@final
class DifferentialTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        DifferentialError,
        DifferentialSuccess,
        DifferentialFailure,
    ]
):
    """Compare student binary output against a reference binary at grading time.

    Unlike ``OutputCompareTest`` (which uses pre-captured expected output),
    ``DifferentialTest`` runs the reference binary fresh for every submission.
    Use this when expected output depends on the student's input files or you
    want to avoid storing a large expected-output corpus.

    ``test_cases`` is typically produced by ``cases_from_matrix`` or a generator::

        test = DifferentialTest(
            "myprogram",
            Path("staff/bin/myprogram"),
            cases_from_matrix(["add", "sub", "mul"], ["1", "10", "100"]),
        )

    Exit codes are not compared by default. Pass ``check_exit_codes=True`` to
    also require the student's exit code to match the reference.
    """

    def __init__(
        self,
        artifact_name: str,
        reference: Path | str,
        test_cases: Iterable[OracleInput],
        options: ExecutableOptions | None = None,
        reference_options: ExecutableOptions | None = None,
        check_exit_codes: bool = False,
    ) -> None:
        self._artifact_name = artifact_name
        self._reference = StaticExecutable([str(reference)])
        self._test_cases = test_cases
        self._options = options
        self._reference_options = reference_options
        self._check_exit_codes = check_exit_codes

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[DifferentialSuccess, DifferentialFailure],
        None,
        Result[dict[str, Artifact], DifferentialError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if artifact is None:
            return Err(
                DifferentialError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact `{self._artifact_name}` not found. "
                        f"Available: {sorted(artifacts)}."
                    ),
                )
            )
        if not isinstance(artifact, FileArtifact):
            return Err(
                DifferentialError(
                    artifact_name=self._artifact_name,
                    message=f"Artifact `{self._artifact_name}` exists but is not a file; cannot execute it.",
                )
            )

        student_opts = self._options or ExecutableOptions()
        ref_opts = self._reference_options or student_opts

        for case in self._test_cases:
            inp = ExecutableInput(stdin_bytes=case.stdin, arguments=case.args)
            student_out = artifact.executable(inp, options=student_opts)
            ref_out = self._reference(inp, options=ref_opts)

            stdout_ok = compare_outputs(
                student_out.stdout_text, ref_out.stdout_text, case.comparison
            )
            exit_ok = (
                not self._check_exit_codes
                or student_out.return_code == ref_out.return_code
            )

            if stdout_ok and exit_ok:
                yield Ok(
                    DifferentialSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                    )
                )
            else:
                yield Err(
                    DifferentialFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        stdin_text=case.stdin.decode("utf-8", errors="replace"),
                        student_stdout=student_out.stdout_text,
                        reference_stdout=ref_out.stdout_text,
                        diff=(
                            _make_diff(ref_out.stdout_text, student_out.stdout_text)
                            if not stdout_ok
                            else ""
                        ),
                        student_exit_code=student_out.return_code,
                        reference_exit_code=ref_out.return_code,
                    )
                )

        return Ok(artifacts)


import lograder.output.layout.test.differential  # noqa: E402, F401
