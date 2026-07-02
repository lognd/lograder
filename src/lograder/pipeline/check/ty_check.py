"""TyCheck  -  run ty static type analysis on Python source files."""

from __future__ import annotations

import re
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckData, CheckError
from lograder.pipeline.types.parcels import Manifest
from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.ty import TyArgs, TyExecutable

# ---------------------------------------------------------------------------
# Packet models
# ---------------------------------------------------------------------------


class TyDiagnostic(BaseModel):
    """A single ty diagnostic line (error or warning)."""

    file: str
    line: int
    column: int
    severity: str  # "error", "warning"
    rule: str | None = None
    message: str


class TyCheckData(CheckData):
    check_name: str = Field(default="ty")
    files: list[str]
    diagnostics: list[TyDiagnostic]


class TyViolation(BaseModel):
    check_name: str = Field(default="ty")
    file: str
    line: int
    column: int
    severity: str
    rule: str | None = None
    message: str


class TyCheckError(CheckError):
    check_name: str = Field(default="ty")
    message: str


# ---------------------------------------------------------------------------
# Diagnostic parser
# ---------------------------------------------------------------------------

# ty --output-format concise: path:line:col: severity[rule] message
_DIAG_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<sev>error|warning)(?:\[(?P<rule>[^\]]+)\])? (?P<msg>.+)$"
)


def _parse_diagnostics(output: str) -> list[TyDiagnostic]:
    diags: list[TyDiagnostic] = []
    for raw_line in output.splitlines():
        m = _DIAG_RE.match(raw_line.strip())
        if m:
            diags.append(
                TyDiagnostic(
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("col")),
                    severity=m.group("sev"),
                    rule=m.group("rule"),
                    message=m.group("msg"),
                )
            )
    return diags


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


@final
class TyCheck(
    Check[
        Manifest,
        Manifest,
        TyCheckError,
        TyCheckData,
        TyViolation,
    ]
):
    """Run ty on the student's Python source files.

    Each type error is yielded as a non-fatal ``Err(TyViolation)`` packet.
    A summary ``Ok(TyCheckData)`` packet is yielded at the end when there
    are no errors.  The step always returns ``Ok(manifest)`` unless ty
    cannot be installed or invoked.

    Example::

        check = TyCheck(files=["graph.py"])
        check.scorer = CleanRunScorer(5.0, label="Type Safety")
        pipeline.add(check)

    Args:
        files:           Python files to check, relative to the submission
                         root.
        python_version:  Python version ty should assume (e.g. ``"3.10"``).
                         Defaults to ty's own detection.
        ignore:          Rule names to suppress (e.g.
                         ``["unresolved-import"]``, ty's analog to mypy's
                         ``ignore_missing_imports`` for code without
                         third-party stubs).
        error:           Rule names to force to error severity.
        warn:            Rule names to force to warning severity.
        extra_args:      Additional ``TyArgs`` overrides.
        options:         ``ExecutableOptions`` forwarded to ty.
    """

    def __init__(
        self,
        files: list[str],
        *,
        python_version: str | None = None,
        ignore: list[str] | None = None,
        error: list[str] | None = None,
        warn: list[str] | None = None,
        extra_args: TyArgs | None = None,
        options: ExecutableOptions | None = None,
    ) -> None:
        self._files = files
        self._python_version = python_version
        self._ignore = ignore or []
        self._error = error or []
        self._warn = warn or []
        self._extra_args = extra_args
        self._options = options

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[TyCheckData, TyViolation],
        None,
        Result[Manifest, TyCheckError],
    ]:
        exe = TyExecutable()
        if exe.check_runnable().is_err:
            install_result = exe.install()
            if install_result.is_err:
                return Err(
                    TyCheckError(
                        message=f"ty is not installed and could not be installed: {install_result.danger_err}"
                    )
                )
            exe.update_base_command(install_result.danger_ok)

        abs_files = [manifest.root / f for f in self._files]
        missing = [str(p) for p in abs_files if not p.exists()]
        if missing:
            return Err(TyCheckError(message=f"File(s) not found: {', '.join(missing)}"))

        base = self._extra_args or TyArgs()
        args = base.model_copy(
            update={
                "files": abs_files,
                "python_version": self._python_version or CLI_ARG_MISSING(),
                "ignore": self._ignore,
                "error": self._error,
                "warn": self._warn,
                "output_format": "concise",
                "color": "never",
                "exit_zero": True,
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
                TyCheckError(message=f"ty invocation failed: {result.danger_err}")
            )

        output = result.danger_ok
        raw = (output.stdout_text or "") + (output.stderr_text or "")
        diagnostics = _parse_diagnostics(raw)
        errors = [d for d in diagnostics if d.severity == "error"]

        for d in errors:
            yield Err(
                TyViolation(
                    file=d.file,
                    line=d.line,
                    column=d.column,
                    severity=d.severity,
                    rule=d.rule,
                    message=d.message,
                )
            )

        if not errors:
            yield Ok(
                TyCheckData(
                    files=self._files,
                    diagnostics=diagnostics,
                )
            )

        return Ok(manifest)


import lograder.output.layout.check.ty  # noqa: E402, F401
