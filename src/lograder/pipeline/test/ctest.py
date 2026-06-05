"""CTestTest  -  run CTest in a CMake build directory and report per-test results."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, CMakeArtifact
from lograder.process.executable import ExecutableInput, ExecutableOptions
from lograder.process.parsers.junit import JUnitTestCase, parse_junit_xml
from lograder.process.registry.ctest import CTestArgs, CTestExecutable

__test__: bool = False


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class CTestSuccess(TestSuccess):
    __test__: bool = False
    suite_name: str
    duration: float | None


class CTestFailure(TestFailure):
    __test__: bool = False
    suite_name: str
    duration: float | None
    failure_message: str
    failure_text: str


class CTestError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class CTestTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        CTestError,
        CTestSuccess,
        CTestFailure,
    ]
):
    """Run CTest inside a CMake build directory and yield one result per test.

    CTest is invoked as::

        ctest --output-junit <tmpfile> [base_args...] --test-dir <build_dir>

    The build directory is resolved in order:

    1. ``build_dir`` constructor parameter (explicit override).
    2. ``artifact_name``  -  looks up the artifact dict for a ``CMakeArtifact``
       and uses its ``.build_dir`` field.

    Both can be provided; ``build_dir`` wins.  Exactly one must be non-``None``.

    ``test_name`` on each packet is ``"SuiteName/TestName"`` when the suite
    differs from the test name, otherwise just the bare name.

    Args:
        artifact_name:  Key for a ``CMakeArtifact`` in the artifacts dict.
                        Used to locate ``build_dir`` when ``build_dir`` is
                        not provided explicitly.  May be ``None`` when
                        ``build_dir`` is given.
        base_args:      Optional ``CTestArgs`` for filtering, parallelism, etc.
                        ``output_junit`` and ``test_dir`` are always overridden.
        build_dir:      Explicit path to the CMake build directory.  Takes
                        precedence over the artifact's ``build_dir``.
        options:        ``ExecutableOptions`` forwarded to ctest.
        warn_no_tests:  Treat a run that produces zero test cases as fatal
                        (default ``True``).
    """

    def __init__(
        self,
        artifact_name: str | None = None,
        base_args: CTestArgs | None = None,
        build_dir: Path | None = None,
        options: ExecutableOptions | None = None,
        warn_no_tests: bool = True,
    ) -> None:
        if artifact_name is None and build_dir is None:
            raise ValueError(
                "CTestTest requires at least one of `artifact_name` or `build_dir`."
            )
        self._artifact_name = artifact_name
        self._base_args = base_args or CTestArgs()
        self._explicit_build_dir = build_dir
        self._options = options or ExecutableOptions()
        self._warn_no_tests = warn_no_tests

    def _resolve_build_dir(
        self, artifacts: dict[str, Artifact]
    ) -> Result[Path, CTestError]:
        if self._explicit_build_dir is not None:
            return Ok(self._explicit_build_dir)

        assert self._artifact_name is not None  # enforced in __init__
        artifact = artifacts.get(self._artifact_name)
        if not isinstance(artifact, CMakeArtifact):
            available = sorted(artifacts)
            return Err(
                CTestError(
                    artifact_name=self._artifact_name or "",
                    message=(
                        f"Artifact '{self._artifact_name}' not found or is not a CMakeArtifact. "
                        f"Available: {available}."
                    ),
                )
            )
        return Ok(artifact.build_dir)

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[CTestSuccess, CTestFailure],
        None,
        Result[dict[str, Artifact], CTestError],
    ]:
        build_dir_result = self._resolve_build_dir(artifacts)
        if build_dir_result.is_err:
            return build_dir_result  # type: ignore[return-value]

        build_dir = build_dir_result.danger_ok

        ctest = CTestExecutable()
        runnable = ctest.check_runnable()
        if runnable.is_err:
            install_result = ctest.install()
            if install_result.is_err:
                return Err(
                    CTestError(
                        artifact_name=self._artifact_name or str(build_dir),
                        message=(
                            f"ctest is not installed and automatic installation failed: "
                            f"{install_result.danger_err}"
                        ),
                    )
                )
            ctest.update_base_command(install_result.danger_ok)

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            out_path = Path(tf.name)

        try:
            args = self._base_args.model_copy(
                update={"output_junit": out_path, "test_dir": build_dir}
            )
            exec_result = ctest(args, ExecutableInput(), self._options)

            if exec_result.is_err:
                return Err(
                    CTestError(
                        artifact_name=self._artifact_name or str(build_dir),
                        message=f"ctest not runnable: {exec_result.danger_err}",
                    )
                )

            raw = exec_result.danger_ok

            try:
                xml_content = out_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                xml_content = ""

            if not xml_content.strip():
                return Err(
                    CTestError(
                        artifact_name=self._artifact_name or str(build_dir),
                        message=(
                            f"CTest produced no JUnit XML (exit {raw.return_code}). "
                            f"stderr: {raw.stderr_text.strip()[:500]}"
                        ),
                    )
                )

            try:
                cases = parse_junit_xml(xml_content)
            except ValueError as exc:
                return Err(
                    CTestError(
                        artifact_name=self._artifact_name or str(build_dir),
                        message=f"Failed to parse CTest JUnit XML: {exc}",
                    )
                )

            if self._warn_no_tests and not cases:
                return Err(
                    CTestError(
                        artifact_name=self._artifact_name or str(build_dir),
                        message="CTest run produced no test cases.",
                    )
                )

            for tc in cases:
                name = _full_name(tc)
                if tc.passed:
                    yield Ok(
                        CTestSuccess(
                            test_name=name,
                            artifact_name=self._artifact_name or str(build_dir),
                            suite_name=tc.suite_name,
                            duration=tc.time,
                        )
                    )
                elif not tc.skipped:
                    yield Err(
                        CTestFailure(
                            test_name=name,
                            artifact_name=self._artifact_name or str(build_dir),
                            suite_name=tc.suite_name,
                            duration=tc.time,
                            failure_message=tc.failure_message
                            or tc.error_message
                            or "",
                            failure_text=tc.failure_text or tc.error_text or "",
                        )
                    )

        finally:
            out_path.unlink(missing_ok=True)

        return Ok(artifacts)


def _full_name(tc: "JUnitTestCase") -> str:
    if tc.suite_name and tc.suite_name != tc.test_name:
        return f"{tc.suite_name}/{tc.test_name}"
    return tc.test_name
