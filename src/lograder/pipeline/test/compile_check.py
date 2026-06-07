"""CompileCheckTest  -  verify that code snippets do or do not compile."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, final

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.gcc import GNUXXStandard, GXXArgs, GXXExecutable

__test__: bool = False


# ---------------------------------------------------------------------------
# Case model
# ---------------------------------------------------------------------------


@dataclass
class CompileCase:
    """A single compilation test case.

    Args:
        name:          Unique case name (used with ``TestCaseScorer``).
        code:          Code snippet to compile.  Wrapped in ``int main() {}``
                       unless ``preamble`` provides a full translation unit.
        should_compile: Whether compilation is expected to succeed.
        preamble:      Code prepended before ``main``  --  use for includes,
                       type definitions, and helper declarations that the
                       snippet depends on.  If ``preamble`` ends with
                       ``"// NO_MAIN"``, no ``main()`` wrapper is added.
        standard:      C++ standard to use (default ``CXX17``).
        extra_flags:   Additional compiler flags for this case.
    """

    name: str
    code: str
    should_compile: bool
    preamble: str = ""
    standard: GNUXXStandard = GNUXXStandard.CXX17
    extra_flags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class CompileCheckSuccess(TestSuccess):
    __test__: bool = False
    should_compile: bool
    compile_message: str


class CompileCheckFailure(TestFailure):
    __test__: bool = False
    should_compile: bool
    compile_message: str
    stderr: str


class CompileCheckError(TestError):
    __test__: bool = False


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


_NO_MAIN_SENTINEL = "// NO_MAIN"


def _build_source(case: CompileCase) -> str:
    if _NO_MAIN_SENTINEL in case.preamble:
        return f"{case.preamble}\n{case.code}\n"
    return f"{case.preamble}\nint main() {{\n{case.code}\n    return 0;\n}}\n"


@final
class CompileCheckTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        CompileCheckError,
        CompileCheckSuccess,
        CompileCheckFailure,
    ]
):
    """Compile code snippets with g++ and assert whether they succeed or fail.

    Each ``CompileCase`` specifies a code snippet and whether it is expected
    to compile.  If the actual outcome matches ``should_compile``, the case
    passes; otherwise it fails.

    This is useful for testing language rules that should be enforced at
    compile time: const correctness, type constraints, deleted constructors,
    access specifiers, template constraints, etc.

    The artifacts dict is passed through unchanged; this step does not
    produce new artifacts.

    Example::

        cases = [
            CompileCase(
                name="const_mutation_forbidden",
                preamble="#include <iostream>",
                code="const int x = 5; x = 10;",
                should_compile=False,
            ),
            CompileCase(
                name="const_read_allowed",
                preamble="#include <iostream>",
                code="const int x = 5; int y = x + 1;",
                should_compile=True,
            ),
        ]
        pipeline.add(cc := CompileCheckTest(cases, include_dirs=[GRADER_DIR]))

    Args:
        cases:        Compilation test cases.
        include_dirs: Extra include directories forwarded to g++ for every case.
        options:      ``ExecutableOptions`` for the g++ invocations.
    """

    _gxx = GXXExecutable()

    def __init__(
        self,
        cases: list[CompileCase],
        *,
        include_dirs: list[Path] | None = None,
        options: ExecutableOptions | None = None,
    ) -> None:
        self._cases = list(cases)
        self._include_dirs = list(include_dirs or [])
        self._options = (options or ExecutableOptions()).model_copy(
            update={
                "stdout_mode": StreamMode.PIPE,
                "stderr_mode": StreamMode.PIPE,
            }
        )

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[CompileCheckSuccess, CompileCheckFailure],
        None,
        Result[dict[str, Artifact], CompileCheckError],
    ]:
        runnable = self._gxx.check_runnable()
        if runnable.is_err:
            return Err(
                CompileCheckError(
                    artifact_name="<compile-check>",
                    message=f"g++ is not available: {runnable.danger_err.message}",
                )
            )

        with tempfile.TemporaryDirectory(prefix="lograder_cc_") as tmpdir:
            tmp = Path(tmpdir)
            for case in self._cases:
                source = _build_source(case)
                src_file = tmp / f"{case.name}.cpp"
                obj_file = tmp / f"{case.name}.o"
                src_file.write_text(source, encoding="utf-8")

                args = GXXArgs(
                    input=[src_file],
                    output=obj_file,
                    standard=case.standard,
                    compile_only=True,
                    include_dirs=self._include_dirs,
                    compile_options=case.extra_flags,
                )
                raw = self._gxx(args, options=self._options)

                if raw.is_err:
                    return Err(
                        CompileCheckError(
                            artifact_name="<compile-check>",
                            message=f"Failed to invoke g++ for case '{case.name}': "
                            f"{raw.danger_err.message}",
                        )
                    )

                out = raw.danger_ok
                compiled = out.return_code == 0

                if compiled == case.should_compile:
                    verb = "compiled" if compiled else "did not compile"
                    yield Ok(
                        CompileCheckSuccess(
                            test_name=case.name,
                            artifact_name="<compile-check>",
                            should_compile=case.should_compile,
                            compile_message=f"As expected: {verb}.",
                        )
                    )
                else:
                    expected = "compile" if case.should_compile else "not compile"
                    actual = "compiled" if compiled else "did not compile"
                    yield Err(
                        CompileCheckFailure(
                            test_name=case.name,
                            artifact_name="<compile-check>",
                            should_compile=case.should_compile,
                            compile_message=f"Expected to {expected}, but {actual}.",
                            stderr=out.stderr_text,
                        )
                    )

        return Ok(artifacts)


import lograder.output.layout.test.compile_check  # noqa: E402, F401
