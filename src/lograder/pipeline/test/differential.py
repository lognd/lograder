import difflib
from collections.abc import Iterable
from pathlib import Path
from typing import Generator, final

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

    The reference binary can be specified in two ways:

    **Static path**  --  a pre-compiled binary shipped with the grader::

        DifferentialTest(
            "myprogram",
            Path("hidden-tests/reference"),
            cases,
        )

    **Artifact key**  --  a binary compiled as a CMake (or other build) target,
    resolved from the same ``dict[str, Artifact]`` at grading time.  Use this
    to avoid committing a pre-compiled binary to the repository::

        DifferentialTest(
            "myprogram",
            reference_artifact="reference",   # key in CMakeBuild output
            test_cases=cases,
        )

    Exactly one of ``reference`` (path) or ``reference_artifact`` (artifact key)
    must be provided.

    Exit codes are not compared by default. Pass ``check_exit_codes=True`` to
    also require the student's exit code to match the reference.
    """

    def __init__(
        self,
        artifact_name: str,
        reference: Path | str | None = None,
        test_cases: Iterable[OracleInput] = (),
        options: ExecutableOptions | None = None,
        reference_options: ExecutableOptions | None = None,
        check_exit_codes: bool = False,
        *,
        reference_artifact: str | None = None,
    ) -> None:
        if reference is None and reference_artifact is None:
            raise ValueError(
                "DifferentialTest: provide either `reference` (path) "
                "or `reference_artifact` (artifact key), not neither."
            )
        if reference is not None and reference_artifact is not None:
            raise ValueError(
                "DifferentialTest: provide either `reference` (path) "
                "or `reference_artifact` (artifact key), not both."
            )
        self._artifact_name = artifact_name
        self._static_reference = (
            StaticExecutable([str(reference)]) if reference is not None else None
        )
        self._reference_artifact = reference_artifact
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

        if self._reference_artifact is not None:
            ref_artifact = artifacts.get(self._reference_artifact)
            if ref_artifact is None:
                return Err(
                    DifferentialError(
                        artifact_name=self._reference_artifact,
                        message=(
                            f"Reference artifact `{self._reference_artifact}` not found. "
                            f"Available: {sorted(artifacts)}."
                        ),
                    )
                )
            if not isinstance(ref_artifact, FileArtifact):
                return Err(
                    DifferentialError(
                        artifact_name=self._reference_artifact,
                        message=f"Reference artifact `{self._reference_artifact}` exists but is not a file; cannot execute it.",
                    )
                )
            reference_exe = ref_artifact.executable
        else:
            assert self._static_reference is not None
            reference_exe = self._static_reference

        student_opts = self._options or ExecutableOptions()
        ref_opts = self._reference_options or student_opts

        for case in self._test_cases:
            inp = ExecutableInput(stdin_bytes=case.stdin, arguments=case.args)
            student_out = artifact.executable(inp, options=student_opts)
            ref_out = reference_exe(inp, options=ref_opts)

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


