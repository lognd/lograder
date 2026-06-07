"""MypyCheck  -  run mypy static type analysis on Python source files."""

from __future__ import annotations

import re
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckData, CheckError
from lograder.pipeline.types.parcels import Manifest
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.mypy import MypyArgs, MypyExecutable

# ---------------------------------------------------------------------------
# Packet models
# ---------------------------------------------------------------------------


class MypyDiagnostic(BaseModel):
    """A single mypy diagnostic line (error, warning, or note)."""

    file: str
    line: int
    column: int
    severity: str  # "error", "warning", "note"
    message: str
    error_code: str | None = None


class MypyCheckData(CheckData):
    check_name: str = Field(default="Mypy")
    files: list[str]
    diagnostics: list[MypyDiagnostic]


class MypyViolation(BaseModel):
    check_name: str = Field(default="Mypy")
    file: str
    line: int
    column: int
    severity: str
    message: str
    error_code: str | None = None


class MypyCheckError(CheckError):
    check_name: str = Field(default="Mypy")
    message: str


# ---------------------------------------------------------------------------
# Diagnostic parser
# ---------------------------------------------------------------------------

# mypy text output: path:line:col: severity: message  [error-code]
_DIAG_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<sev>error|warning|note): (?P<msg>.+?)(?:\s+\[(?P<code>[^\]]+)\])?$"
)


def _parse_diagnostics(output: str) -> list[MypyDiagnostic]:
    diags: list[MypyDiagnostic] = []
    for raw_line in output.splitlines():
        m = _DIAG_RE.match(raw_line.strip())
        if m:
            diags.append(
                MypyDiagnostic(
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("col")),
                    severity=m.group("sev"),
                    message=m.group("msg"),
                    error_code=m.group("code"),
                )
            )
    return diags


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class MypyCheck(
    Check[
        Manifest,
        Manifest,
        MypyCheckError,
        MypyCheckData,
        MypyViolation,
    ]
):
    """Run mypy on the student's Python source files.

    Each type error is yielded as a non-fatal ``Err(MypyViolation)`` packet.
    A summary ``Ok(MypyCheckData)`` packet is yielded at the end when there
    are no errors.  The step always returns ``Ok(manifest)`` unless mypy
    cannot be installed or invoked.

    Example::

        check = MypyCheck(
            files=["graph.py"],
            strict=True,
        )
        check.scorer = CleanRunScorer(5.0, label="Type Safety")
        pipeline.add(check)

    Args:
        files:                    Python files to check, relative to the
                                  submission root.
        strict:                   Enable mypy ``--strict`` mode.
        disallow_untyped_defs:    Require type annotations on all functions.
        disallow_incomplete_defs: Require complete annotations.
        check_untyped_defs:       Type-check bodies of unannotated functions.
        ignore_missing_imports:   Suppress errors for missing stubs/modules.
        extra_args:               Additional ``MypyArgs`` overrides.
        options:                  ``ExecutableOptions`` forwarded to mypy.
    """

    def __init__(
        self,
        files: list[str],
        *,
        strict: bool = False,
        disallow_untyped_defs: bool = False,
        disallow_incomplete_defs: bool = False,
        check_untyped_defs: bool = False,
        ignore_missing_imports: bool = True,
        extra_args: MypyArgs | None = None,
        options: ExecutableOptions | None = None,
    ) -> None:
        self._files = files
        self._strict = strict
        self._disallow_untyped_defs = disallow_untyped_defs
        self._disallow_incomplete_defs = disallow_incomplete_defs
        self._check_untyped_defs = check_untyped_defs
        self._ignore_missing_imports = ignore_missing_imports
        self._extra_args = extra_args
        self._options = options

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[MypyCheckData, MypyViolation],
        None,
        Result[Manifest, MypyCheckError],
    ]:
        exe = MypyExecutable()
        if exe.check_runnable().is_err:
            install_result = exe.install()
            if install_result.is_err:
                return Err(
                    MypyCheckError(
                        message=f"mypy is not installed and could not be installed: {install_result.danger_err}"
                    )
                )
            exe.update_base_command(install_result.danger_ok)

        abs_files = [manifest.root / f for f in self._files]
        missing = [str(p) for p in abs_files if not p.exists()]
        if missing:
            return Err(
                MypyCheckError(message=f"File(s) not found: {', '.join(missing)}")
            )

        base = self._extra_args or MypyArgs()
        args = base.model_copy(
            update={
                "files": abs_files,
                "strict": self._strict,
                "disallow_untyped_defs": self._disallow_untyped_defs,
                "disallow_incomplete_defs": self._disallow_incomplete_defs,
                "check_untyped_defs": self._check_untyped_defs,
                "ignore_missing_imports": self._ignore_missing_imports,
                "no_color_output": True,
                "show_error_codes": True,
                "show_column_numbers": True,
                "no_error_summary": True,
            }
        )

        run_options = (self._options or ExecutableOptions()).model_copy(
            update={
                "cwd": manifest.root,
                "stdout_mode": StreamMode.PIPE,
                "stderr_mode": StreamMode.PIPE,
            }
        )

        result = exe(args, options=run_options)
        if result.is_err:
            return Err(
                MypyCheckError(message=f"mypy invocation failed: {result.danger_err}")
            )

        output = result.danger_ok
        raw = (output.stdout_text or "") + (output.stderr_text or "")
        diagnostics = _parse_diagnostics(raw)
        errors = [d for d in diagnostics if d.severity == "error"]

        for d in errors:
            yield Err(
                MypyViolation(
                    file=d.file,
                    line=d.line,
                    column=d.column,
                    severity=d.severity,
                    message=d.message,
                    error_code=d.error_code,
                )
            )

        if not errors:
            yield Ok(
                MypyCheckData(
                    files=self._files,
                    diagnostics=diagnostics,
                )
            )

        return Ok(manifest)


import lograder.output.layout.check.mypy  # noqa: E402, F401
