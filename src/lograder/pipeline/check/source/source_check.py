from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Generator, Literal

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckData, CheckError
from lograder.pipeline.check.source._ast import (
    CppAnalysis,
    PreprocessError,
    PythonAnalysis,
    analyze_cpp,
    analyze_python,
)
from lograder.pipeline.types.parcels import Manifest

Language = Literal["c", "cpp", "python"]


# ---------------------------------------------------------------------------
# Constraint types
# ---------------------------------------------------------------------------


class OperatorConstraint(BaseModel):
    """Limit occurrences of one or more operator tokens (combined count)."""

    tokens: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{t}`" for t in self.tokens)


class IdentifierConstraint(BaseModel):
    """Limit uses of specific identifiers/names (variables, functions, types).

    Matched against ``identifier`` and ``type_identifier`` nodes in C/C++,
    and ``identifier`` nodes in Python  -  after macro expansion for C/C++.
    """

    names: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{n}`" for n in self.names)


class QualifiedNameConstraint(BaseModel):
    """C/C++ only: limit uses of fully-qualified names such as ``std::vector``.

    Matched against ``qualified_identifier`` nodes after macro expansion.
    Names are specified with ``::`` separators (e.g. ``"std::vector"``).
    """

    qualified_names: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{n}`" for n in self.qualified_names)


class IncludeConstraint(BaseModel):
    """C/C++ only: limit ``#include`` directives for specific headers.

    Headers are matched as they appear in source, including angle brackets or
    quotes  -  e.g. ``"<vector>"`` or ``'"mylib.h"'``.  Checked on the
    *original* (unpreprocessed) source so that includes are still visible.
    """

    headers: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(self.headers)


class ImportConstraint(BaseModel):
    """Python only: limit ``import`` / ``from ... import`` statements by module.

    Matches the top-level package name and any dotted sub-path recorded during
    the walk  -  e.g. ``"numpy"`` matches ``import numpy``, ``import numpy.random``,
    and ``from numpy.random import choice``.
    """

    modules: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{m}`" for m in self.modules)


AnyConstraint = (
    OperatorConstraint
    | IdentifierConstraint
    | QualifiedNameConstraint
    | IncludeConstraint
    | ImportConstraint
)


# ---------------------------------------------------------------------------
# Display / error models
# ---------------------------------------------------------------------------


class ConstraintResult(BaseModel):
    label: str
    count: int
    max_count: int


class SourceCheckData(CheckData):
    check_name: str = Field(default="Source Check")
    file: str
    results: list[ConstraintResult]


class SourceViolation(BaseModel):
    check_name: str = Field(default="Source Check")
    file: str
    label: str
    count: int
    max_count: int


class SourceCheckError(CheckError):
    check_name: str = Field(default="Source Check")
    file: str
    message: str


# ---------------------------------------------------------------------------
# Helper: apply constraints against analysis results
# ---------------------------------------------------------------------------


def _apply_constraints(
    constraints: list[AnyConstraint],
    cpp: CppAnalysis | None,
    py: PythonAnalysis | None,
) -> list[tuple[AnyConstraint, int]]:
    """Return (constraint, combined_count) pairs for every constraint."""
    results: list[tuple[AnyConstraint, int]] = []
    for c in constraints:
        count: int
        if isinstance(c, OperatorConstraint):
            src = (
                cpp.operators
                if cpp is not None
                else (py.operators if py is not None else Counter())
            )
            count = sum(src.get(tok, 0) for tok in c.tokens)
        elif isinstance(c, IdentifierConstraint):
            src = (
                cpp.identifiers
                if cpp is not None
                else (py.identifiers if py is not None else Counter())
            )
            count = sum(src.get(name, 0) for name in c.names)
        elif isinstance(c, QualifiedNameConstraint):
            src = cpp.qualified_names if cpp is not None else Counter()
            count = sum(src.get(qn, 0) for qn in c.qualified_names)
        elif isinstance(c, IncludeConstraint):
            src = cpp.includes if cpp is not None else Counter()
            count = sum(src.get(h, 0) for h in c.headers)
        elif isinstance(c, ImportConstraint):
            src = py.imports if py is not None else Counter()
            count = sum(src.get(m, 0) for m in c.modules)
        else:
            count = 0
        results.append((c, count))
    return results


# ---------------------------------------------------------------------------
# Check step
# ---------------------------------------------------------------------------


class SourceCheck(
    Check[
        Manifest,
        Manifest,
        SourceCheckError,
        SourceCheckData,
        SourceViolation,
    ]
):
    """Check source files for constraint violations using a language-aware AST.

    Supported constraint types
    --------------------------
    - ``OperatorConstraint``      -  operators (both languages)
    - ``IdentifierConstraint``    -  names / identifiers (both languages)
    - ``QualifiedNameConstraint`` -  ``std::vector``-style names (C/C++ only)
    - ``IncludeConstraint``       -  ``#include`` directives (C/C++ only)
    - ``ImportConstraint``        -  ``import`` statements (Python only)

    C/C++ files are preprocessed first so ``#define`` aliasing is resolved
    before the AST is built.  Violations are yielded as non-fatal ``Err``
    packets (one per violated constraint per file); the step always returns
    ``Ok(manifest)`` unless a fatal error occurs (file missing, preprocessing
    failed, unreadable file).
    """

    def __init__(
        self,
        files: list[str],
        constraints: list[AnyConstraint],
        language: Language,
        include_dirs: list[Path] | None = None,
        label: str = "Source Check",
    ) -> None:
        self._files = files
        self._constraints = constraints
        self._language: Language = language
        self._include_dirs: list[Path] = include_dirs or []
        self._label = label

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[SourceCheckData, SourceViolation],
        None,
        Result[Manifest, SourceCheckError],
    ]:
        for file_name in self._files:
            path = manifest.root / file_name
            if not path.exists():
                return Err(
                    SourceCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"File not found: {path}",
                    )
                )

            cpp_analysis: CppAnalysis | None = None
            py_analysis: PythonAnalysis | None = None

            if self._language in ("c", "cpp"):
                cpp_result = analyze_cpp(path, self._include_dirs or None)
                if cpp_result.is_err:
                    return Err(
                        SourceCheckError(
                            check_name=self._label,
                            file=file_name,
                            message=cpp_result.danger_err.message,
                        )
                    )
                cpp_analysis = cpp_result.danger_ok
            else:
                py_result = analyze_python(path)
                if py_result.is_err:
                    return Err(
                        SourceCheckError(
                            check_name=self._label,
                            file=file_name,
                            message=str(py_result.danger_err),
                        )
                    )
                py_analysis = py_result.danger_ok

            pairs = _apply_constraints(self._constraints, cpp_analysis, py_analysis)
            constraint_results: list[ConstraintResult] = []
            any_violation = False

            for constraint, count in pairs:
                constraint_results.append(
                    ConstraintResult(
                        label=constraint.display_label,
                        count=count,
                        max_count=constraint.max_count,
                    )
                )
                if count > constraint.max_count:
                    any_violation = True
                    yield Err(
                        SourceViolation(
                            check_name=self._label,
                            file=file_name,
                            label=constraint.display_label,
                            count=count,
                            max_count=constraint.max_count,
                        )
                    )

            if not any_violation:
                yield Ok(
                    SourceCheckData(
                        check_name=self._label,
                        file=file_name,
                        results=constraint_results,
                    )
                )

        return Ok(manifest)


import lograder.output.layout.check.source  # noqa: E402, F401
