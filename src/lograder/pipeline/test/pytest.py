"""PytestTest  -  run pytest and report per-test results via JUnit XML."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableInput, ExecutableOptions
from lograder.process.parsers.junit import JUnitTestCase, parse_junit_xml
from lograder.process.registry.pytest import PytestArgs, PytestExecutable

__test__: bool = False


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class PytestSuccess(TestSuccess):
    __test__: bool = False
    classname: str
    duration: float | None
    stdout: str
    stderr: str


class PytestFailure(TestFailure):
    __test__: bool = False
    classname: str
    duration: float | None
    failure_message: str
    failure_text: str
    stdout: str
    stderr: str


class PytestError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class PytestTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        PytestError,
        PytestSuccess,
        PytestFailure,
    ]
):
    """Run pytest and yield one result packet per test case.

    pytest is invoked as::

        pytest --junitxml=<tmpfile> [paths...] [base_args...]

    The JUnit XML is parsed after the run; each ``<testcase>`` becomes an
    ``Ok(PytestSuccess)`` or ``Err(PytestFailure)`` yield.  Skipped tests
    are silently ignored.

    Unlike the binary-based test steps, ``PytestTest`` does not look up an
    artifact by name  -  it invokes the ``pytest`` executable directly.  Use
    ``options.cwd`` to point pytest at the submission directory.

    ``test_name`` on each packet is ``"classname::name"``  -  matching pytest's
    native ``module::function`` naming convention.  Use this value with
    ``TestCaseScorer``.

    Args:
        paths:         Paths to test files or directories to collect, relative
                       to ``options.cwd`` (or absolute).  If ``None``, pytest
                       discovers tests in ``options.cwd``.  Paths are resolved
                       at call time, not at construction.
        base_args:     Optional ``PytestArgs`` for filtering, verbosity, etc.
                       ``junit_xml`` and ``paths`` are always overridden.
                       Do not put paths in ``base_args.paths``; they are
                       validated at construction time and may not yet exist.
        options:       ``ExecutableOptions`` forwarded to pytest.  Set ``cwd``
                       to the submission directory.
        warn_no_tests: Treat a run that produces zero test cases as fatal
                       (default ``True``).
        label:         Used as ``artifact_name`` in result packets (default
                       ``"pytest"``).
    """

    def __init__(
        self,
        paths: list[str | Path] | None = None,
        base_args: PytestArgs | None = None,
        options: ExecutableOptions | None = None,
        warn_no_tests: bool = True,
        label: str = "pytest",
    ) -> None:
        self._raw_paths = [Path(p) for p in paths] if paths is not None else None
        self._base_args = base_args or PytestArgs()
        self._options = options or ExecutableOptions()
        self._warn_no_tests = warn_no_tests
        self._label = label

    def _resolve_paths(self) -> list[Path]:
        """Resolve paths relative to options.cwd at call time."""
        if self._raw_paths is None:
            return []
        cwd = self._options.cwd
        return [p if p.is_absolute() else cwd / p for p in self._raw_paths]

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[PytestSuccess, PytestFailure],
        None,
        Result[dict[str, Artifact], PytestError],
    ]:
        pytest_exec = PytestExecutable()
        runnable = pytest_exec.check_runnable()
        if runnable.is_err:
            install_result = pytest_exec.install()
            if install_result.is_err:
                return Err(
                    PytestError(
                        artifact_name=self._label,
                        message=(
                            f"pytest is not installed and automatic installation failed: "
                            f"{install_result.danger_err}"
                        ),
                    )
                )
            pytest_exec.update_base_command(install_result.danger_ok)

        resolved_paths = self._resolve_paths()

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            out_path = Path(tf.name)

        try:
            args = self._base_args.model_copy(
                update={"junit_xml": out_path, "paths": resolved_paths}
            )
            exec_result = pytest_exec(args, ExecutableInput(), self._options)

            if exec_result.is_err:
                return Err(
                    PytestError(
                        artifact_name=self._label,
                        message=f"pytest not runnable: {exec_result.danger_err}",
                    )
                )

            raw = exec_result.danger_ok

            try:
                xml_content = out_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                xml_content = ""

            if not xml_content.strip():
                return Err(
                    PytestError(
                        artifact_name=self._label,
                        message=(
                            f"pytest produced no JUnit XML (exit {raw.return_code}). "
                            f"stderr: {raw.stderr_text.strip()[:500]}"
                        ),
                    )
                )

            try:
                cases = parse_junit_xml(xml_content)
            except ValueError as exc:
                return Err(
                    PytestError(
                        artifact_name=self._label,
                        message=f"Failed to parse pytest JUnit XML: {exc}",
                    )
                )

            if self._warn_no_tests and not cases:
                return Err(
                    PytestError(
                        artifact_name=self._label,
                        message="pytest run produced no test cases.",
                    )
                )

            for tc in cases:
                name = _full_name(tc)
                if tc.passed:
                    yield Ok(
                        PytestSuccess(
                            test_name=name,
                            artifact_name=self._label,
                            classname=tc.classname,
                            duration=tc.time,
                            stdout=tc.stdout,
                            stderr=tc.stderr,
                        )
                    )
                elif not tc.skipped:
                    yield Err(
                        PytestFailure(
                            test_name=name,
                            artifact_name=self._label,
                            classname=tc.classname,
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
    """'classname::name' matching pytest's native naming."""
    if tc.classname and tc.classname != tc.test_name:
        return f"{tc.classname}::{tc.test_name}"
    return tc.test_name
