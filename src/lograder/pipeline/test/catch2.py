"""Catch2Test  -  run a Catch2 test binary and report per-test results."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import (
    JUnitTestError,
    JUnitTestFailure,
    JUnitTestSuccess,
    Test,
)
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import ExecutableInput, ExecutableOptions
from lograder.process.parsers.junit import JUnitTestCase, parse_junit_xml

__test__: bool = False


# ---------------------------------------------------------------------------
# CLIArgs for Catch2 test binaries
# ---------------------------------------------------------------------------


class Catch2Args(CLIArgs):
    """Arguments for a Catch2 v3 test executable.

    ``reporter`` and ``out`` are managed by ``Catch2Test``; override them
    only when constructing args for manual invocation outside the step.
    """

    # -- Reporting --------------------------------------------------------------
    reporter: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--reporter", "{}"]
    )
    out: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--out", "{}"]
    )

    # -- Test selection ---------------------------------------------------------
    # Free-form test spec: test name glob, tag expression, or combination.
    # e.g. "[math]", "my test name", "[unit] ~[slow]"
    test_spec: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["{}"], position=-1
    )

    # -- Execution --------------------------------------------------------------
    abort: bool = CLIPresenceFlag(["--abort"], default=False)
    abortx: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--abortx", "{}"]
    )
    order: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--order", "{}"]
    )
    rng_seed: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--rng-seed", "{}"]
    )
    # Pass "NoTests" to fail when no tests are matched
    warn: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--warn", "{}"]
    )

    # -- Output -----------------------------------------------------------------
    durations: bool = CLIPresenceFlag(["--durations", "yes"], default=False)
    min_duration: float | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--min-duration", "{}"]
    )
    verbosity: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--verbosity", "{}"]
    )

    # -- Sharding (v3.3+) -------------------------------------------------------
    shard_count: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--shard-count", "{}"]
    )
    shard_index: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--shard-index", "{}"]
    )

    # -- Informational ----------------------------------------------------------
    list_tests: bool = CLIPresenceFlag(["--list-tests"], default=False)
    list_tags: bool = CLIPresenceFlag(["--list-tags"], default=False)
    list_reporters: bool = CLIPresenceFlag(["--list-reporters"], default=False)


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class Catch2Success(JUnitTestSuccess):
    suite_name: str
    stdout: str
    stderr: str


class Catch2Failure(JUnitTestFailure):
    suite_name: str
    stdout: str
    stderr: str


class Catch2Error(JUnitTestError):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_name(tc: JUnitTestCase) -> str:
    """'SuiteName/TestName' when suite differs from name, otherwise just name."""
    if tc.suite_name and tc.suite_name != tc.test_name:
        return f"{tc.suite_name}/{tc.test_name}"
    return tc.test_name


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class Catch2Test(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        Catch2Error,
        Catch2Success,
        Catch2Failure,
    ]
):
    """Run a Catch2 test binary and yield one result packet per test case.

    The binary is invoked as::

        <artifact> --reporter junit --out <tmpfile> [base_args...]

    The JUnit XML is parsed after the run; each ``<testcase>`` becomes an
    ``Ok(Catch2Success)`` or ``Err(Catch2Failure)`` yield.  Skipped tests
    are silently ignored.

    ``test_name`` on each packet is ``"SuiteName/TestName"`` when the suite
    name differs from the test name, otherwise just the bare name  -  use this
    value with ``TestCaseScorer``.

    Args:
        artifact_name:  Key in the artifacts dict for the Catch2 binary.
        base_args:      Optional ``Catch2Args`` for test filtering, ordering,
                        sharding, etc.  ``reporter`` and ``out`` are always
                        overridden internally.
        options:        ``ExecutableOptions`` forwarded to the binary.
        warn_no_tests:  Treat a run that produces zero test cases as fatal
                        (default ``True``).
    """

    def __init__(
        self,
        artifact_name: str,
        base_args: Catch2Args | None = None,
        options: ExecutableOptions | None = None,
        warn_no_tests: bool = True,
    ) -> None:
        self._artifact_name = artifact_name
        self._base_args = base_args or Catch2Args()
        self._options = options or ExecutableOptions()
        self._warn_no_tests = warn_no_tests

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[Catch2Success, Catch2Failure],
        None,
        Result[dict[str, Artifact], Catch2Error],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if not isinstance(artifact, FileArtifact):
            return Err(
                Catch2Error(
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
                update={"reporter": "junit", "out": out_path}
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
                    Catch2Error(
                        artifact_name=self._artifact_name,
                        message=(
                            f"Catch2 produced no JUnit XML (exit {raw.return_code}). "
                            f"stderr: {raw.stderr_text.strip()[:500]}"
                        ),
                    )
                )

            try:
                cases = parse_junit_xml(xml_content)
            except ValueError as exc:
                return Err(
                    Catch2Error(
                        artifact_name=self._artifact_name,
                        message=f"Failed to parse Catch2 JUnit XML: {exc}",
                    )
                )

            if self._warn_no_tests and not cases:
                return Err(
                    Catch2Error(
                        artifact_name=self._artifact_name,
                        message="Catch2 run produced no test cases.",
                    )
                )

            for tc in cases:
                name = _full_name(tc)
                if tc.passed:
                    yield Ok(
                        Catch2Success(
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
                        Catch2Failure(
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


