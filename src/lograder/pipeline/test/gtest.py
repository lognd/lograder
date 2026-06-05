"""GTestTest  -  run a Google Test binary and report per-test results."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.executable import ExecutableInput, ExecutableOptions
from lograder.process.parsers.junit import JUnitTestCase, parse_junit_xml
from lograder.process.registry.gtest import GTestArgs

__test__: bool = False


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class GTestSuccess(TestSuccess):
    __test__: bool = False
    suite_name: str
    duration: float | None
    stdout: str
    stderr: str


class GTestFailure(TestFailure):
    __test__: bool = False
    suite_name: str
    duration: float | None
    failure_message: str
    failure_text: str
    stdout: str
    stderr: str


class GTestError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class GTestTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        GTestError,
        GTestSuccess,
        GTestFailure,
    ]
):
    """Run a Google Test binary and yield one result packet per test case.

    The binary is invoked as::

        <artifact> --gtest_output=xml:<tmpfile> [base_args...]

    The JUnit XML is parsed after the run; each ``<testcase>`` becomes an
    ``Ok(GTestSuccess)`` or ``Err(GTestFailure)`` yield.  Skipped/disabled
    tests are silently ignored.

    ``test_name`` on each packet uses the format ``"SuiteName.TestName"``  -
    matching Google Test's native ``SUITE.TEST`` naming convention.  Use this
    value with ``TestCaseScorer``.

    Args:
        artifact_name:  Key in the artifacts dict for the gtest binary.
        base_args:      Optional ``GTestArgs`` for filtering, repetition,
                        shuffling, etc.  ``gtest_output`` is always overridden.
        options:        ``ExecutableOptions`` forwarded to the binary.
        warn_no_tests:  Treat a run that produces zero test cases as fatal
                        (default ``True``).
    """

    def __init__(
        self,
        artifact_name: str,
        base_args: GTestArgs | None = None,
        options: ExecutableOptions | None = None,
        warn_no_tests: bool = True,
    ) -> None:
        self._artifact_name = artifact_name
        self._base_args = base_args or GTestArgs()
        self._options = options or ExecutableOptions()
        self._warn_no_tests = warn_no_tests

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[GTestSuccess, GTestFailure],
        None,
        Result[dict[str, Artifact], GTestError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if not isinstance(artifact, FileArtifact):
            return Err(
                GTestError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact '{self._artifact_name}' not found or is not a FileArtifact. "
                        f"Available: {sorted(artifacts)}."
                    ),
                )
            )

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            out_path = Path(tf.name)

        try:
            args = self._base_args.model_copy(
                update={"gtest_output": f"xml:{out_path}"}
            )
            raw = artifact.executable(
                ExecutableInput(arguments=args.emit()), options=self._options
            )

            try:
                xml_content = out_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                xml_content = ""

            if not xml_content.strip():
                return Err(
                    GTestError(
                        artifact_name=self._artifact_name,
                        message=(
                            f"Google Test produced no JUnit XML (exit {raw.return_code}). "
                            f"stderr: {raw.stderr_text.strip()[:500]}"
                        ),
                    )
                )

            try:
                cases = parse_junit_xml(xml_content)
            except ValueError as exc:
                return Err(
                    GTestError(
                        artifact_name=self._artifact_name,
                        message=f"Failed to parse Google Test JUnit XML: {exc}",
                    )
                )

            if self._warn_no_tests and not cases:
                return Err(
                    GTestError(
                        artifact_name=self._artifact_name,
                        message="Google Test run produced no test cases.",
                    )
                )

            for tc in cases:
                name = _full_name(tc)
                if tc.passed:
                    yield Ok(
                        GTestSuccess(
                            test_name=name,
                            artifact_name=self._artifact_name,
                            suite_name=tc.suite_name,
                            duration=tc.time,
                            stdout=tc.stdout,
                            stderr=tc.stderr,
                        )
                    )
                elif not tc.skipped:
                    yield Err(
                        GTestFailure(
                            test_name=name,
                            artifact_name=self._artifact_name,
                            suite_name=tc.suite_name,
                            duration=tc.time,
                            failure_message=tc.failure_message
                            or tc.error_message
                            or "",
                            failure_text=tc.failure_text or tc.error_text or "",
                            stdout=tc.stdout,
                            stderr=tc.stderr,
                        )
                    )

        finally:
            out_path.unlink(missing_ok=True)

        return Ok(artifacts)


def _full_name(tc: JUnitTestCase) -> str:
    """'SuiteName.TestName' matching gtest's native naming."""
    if tc.suite_name and tc.suite_name != tc.test_name:
        return f"{tc.suite_name}.{tc.test_name}"
    return tc.test_name


import lograder.output.layout.test.gtest  # noqa: E402, F401
