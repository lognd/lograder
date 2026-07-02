"""ASanTest  -  run test cases under an AddressSanitizer-instrumented binary."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.config import get_config
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode

__test__: bool = False

# AddressSanitizer error patterns found in stderr
_ASAN_ERROR_RE = re.compile(
    r"(=+ERROR: (AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer)"
    r"|SUMMARY: (AddressSanitizer|LeakSanitizer): )",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Case model
# ---------------------------------------------------------------------------


@dataclass
class ASanCase:
    """A single test case for an AddressSanitizer-instrumented binary.

    Args:
        name:   Unique case name (used with ``TestCaseScorer``).
        args:   Command-line arguments.
        stdin:  Standard input bytes (or str, auto-encoded to UTF-8).
        expected_exit_code:  If set, also assert the exit code matches.
    """

    name: str
    args: list[str] = field(default_factory=list)
    stdin: bytes | str = b""
    expected_exit_code: int | None = None


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class ASanSuccess(TestSuccess):
    __test__: bool = False
    args: list[str]
    exit_code: int


class ASanFailure(TestFailure):
    __test__: bool = False
    args: list[str]
    exit_code: int
    asan_report: str
    expected_exit_code: int | None


class ASanError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class ASanTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        ASanError,
        ASanSuccess,
        ASanFailure,
    ]
):
    """Run test cases against an AddressSanitizer-instrumented binary.

    For each case the binary is executed and its stderr is scanned for ASan
    error patterns.  A case passes if no ASan errors are found (and,
    optionally, the exit code matches).

    The binary **must** have been compiled with ``-fsanitize=address`` (and
    optionally ``-fsanitize=undefined``).  Use ``GXXBuild`` with
    ``sanitizers=["address"]`` or add the flags to your ``CMakeLists.txt``.

    The artifacts dict is passed through unchanged.

    Example::

        pipeline.add(GXXBuild(
            sources=["student.cpp"],
            output="student",
            sanitizers=["address", "undefined"],
        ))
        pipeline.add(asan := ASanTest("student", [
            ASanCase("heap_no_overflow",  args=["10"], stdin=b""),
            ASanCase("stack_no_overflow", args=["5"],  stdin=b""),
        ]))
        asan.scorer = AllOrNothingScorer(10.0, label="Memory safety")

    Args:
        artifact_name:  Key in the artifacts dict for the instrumented binary.
        cases:          Test cases to run.
        options:        ``ExecutableOptions`` forwarded to each run.
    """

    def __init__(
        self,
        artifact_name: str,
        cases: Iterable[ASanCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._cases = list(cases)
        self._options = options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[ASanSuccess, ASanFailure],
        None,
        Result[dict[str, Artifact], ASanError],
    ]:
        artifact_result = self._resolve_artifact(artifacts, self._artifact_name)
        if artifact_result.is_err:
            return Err(
                ASanError(
                    artifact_name=self._artifact_name,
                    message=artifact_result.danger_err,
                )
            )
        artifact = artifact_result.danger_ok

        cfg = get_config()
        base_options = (self._options or ExecutableOptions()).model_copy(
            update={
                "stdout_mode": StreamMode.PIPE,
                "stderr_mode": StreamMode.PIPE,
                "timeout": cfg.executable_timeout,
            }
        )

        for case in self._cases:
            stdin_bytes = (
                case.stdin.encode("utf-8")
                if isinstance(case.stdin, str)
                else case.stdin
            )
            out = self._invoke(artifact, case.args, stdin_bytes, base_options)

            stderr = out.stderr_text
            asan_hit = _ASAN_ERROR_RE.search(stderr) is not None

            exit_code_ok = (
                case.expected_exit_code is None
                or out.return_code == case.expected_exit_code
            )

            if not asan_hit and exit_code_ok:
                yield Ok(
                    ASanSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        exit_code=out.return_code,
                    )
                )
            else:
                report_lines: list[str] = []
                if asan_hit:
                    # Extract the relevant portion of the ASan report
                    idx = stderr.find("ERROR:")
                    if idx == -1:
                        idx = 0
                    report_lines.append(stderr[idx : idx + 2000].rstrip())
                if not exit_code_ok:
                    report_lines.append(
                        f"Exit code: expected {case.expected_exit_code}, "
                        f"got {out.return_code}."
                    )
                yield Err(
                    ASanFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        exit_code=out.return_code,
                        asan_report="\n".join(report_lines),
                        expected_exit_code=case.expected_exit_code,
                    )
                )

        return Ok(artifacts)


import lograder.output.layout.test.asan  # noqa: E402, F401
